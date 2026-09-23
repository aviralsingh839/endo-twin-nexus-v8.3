package org.chronopcos.patient.learning

import android.content.Context
import kotlin.math.abs
import kotlin.math.exp
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sqrt
import org.json.JSONArray
import org.json.JSONObject

/**
 * Continual self-learning layer, Kotlin mirror of `src/core/adaptive_learning.py`.
 *
 * The wearable model keeps learning for as long as the device is worn and upgrades
 * itself through a capability ladder once the evidence is there:
 *
 *  - `population`    : nothing personal yet, population priors only
 *  - `personalized`  : robust personal norms (median / MAD) and z-scores
 *  - `circadian`     : time-of-day conditioned norms
 *  - `adaptive`      : a persistent shift becomes the new normal, a short excursion
 *                      is frozen out of the baseline and never learned away
 *
 * A supervised head unlocks separately, and only when it beats a base-rate predictor
 * on labels it has not been trained on. If it cannot, it stays `WITHHELD` and says so.
 *
 * HONEST STATUS: this file mirrors the Python reference implementation, which is the
 * tested one. It has NOT been compiled or run here - this environment has no Android
 * SDK, Gradle or connected device. Treat it as review-only code until a device build
 * is run. The maths and the gate thresholds are intentionally identical to the Python
 * version so the two can be compared line by line.
 *
 * Privacy: all state is local (SharedPreferences on the device). Nothing is uploaded.
 * Everything emitted is a description of data the user's own device collected.
 */
object LearningContract {
    const val SCHEMA = "endo_twin.adaptive_wearable/1"
    const val DISCLAIMER =
        "Engineering learning layer on a research prototype. Not a diagnosis, not a medical device, " +
            "not clinically validated. Confidence describes data coverage, not clinical certainty."
}

val LEARNING_METRICS = listOf(
    "hr_bpm", "resting_hr_bpm", "rmssd_ms", "skin_temp_c", "activity_level"
)

val METRIC_BOUNDS: Map<String, ClosedFloatingPointRange<Double>> = mapOf(
    "hr_bpm" to 25.0..240.0,
    "resting_hr_bpm" to 25.0..200.0,
    "rmssd_ms" to 1.0..400.0,
    "skin_temp_c" to 15.0..43.0,
    "activity_level" to 0.0..1.0
)

val POPULATION_PRIOR: Map<String, Pair<Double, Double>> = mapOf(
    "hr_bpm" to (72.0 to 12.0),
    "resting_hr_bpm" to (62.0 to 9.0),
    "rmssd_ms" to (42.0 to 15.0),
    "skin_temp_c" to (32.5 to 0.7),
    "activity_level" to (0.10 to 0.08)
)

val TIERS = listOf("population", "personalized", "circadian", "adaptive")

val TIER_HEADLINES = mapOf(
    "population" to "Population reference only - the model has not met this wearer yet.",
    "personalized" to "Personal norms active: deviations are measured against you, not the population.",
    "circadian" to "Time-of-day norms active: values are compared with the same hour of previous days.",
    "adaptive" to "Drift-aware: a persistent shift becomes the new normal, a transient event does not."
)

data class LearningConfig(
    val maxWornGapSeconds: Double = 300.0,
    val saveEvery: Int = 60,
    val reservoirSize: Int = 1024,
    val bucketSize: Int = 256,
    val recalcEvery: Int = 30,
    val recentWindow: Int = 128,
    val historyLimit: Int = 200,
    val normInitSamples: Int = 300,
    val normInitSpanSeconds: Double = 12 * 3600.0,
    val normInitMinQuality: Double = 0.50,
    val personalMinWornSeconds: Double = 3600.0,
    val personalMinMetricSamples: Int = 120,
    val personalMinQuality: Double = 0.50,
    val personalMinMetrics: Int = 4,
    val circadianMinWornSeconds: Double = 86400.0,
    val circadianMinDays: Int = 2,
    val circadianBucketMin: Int = 30,
    val circadianMinBuckets: Int = 6,
    val adaptiveMinWornSeconds: Double = 3 * 86400.0,
    val adaptiveMinDays: Int = 3,
    val adaptiveMinMetricSamples: Int = 500,
    val adaptiveMinMetrics: Int = 3,
    val phDeltaSigma: Double = 0.25,
    val phLambdaSigma: Double = 8.0,
    val driftMinPersistenceSeconds: Double = 6 * 3600.0,
    val driftWindowSigma: Double = 1.5,
    val driftMinShiftSigma: Double = 1.5,
    val quietResetSamples: Int = 30,
    val maxAdaptSigmaPerHour: Double = 0.35,
    val maxAbsorbSigma: Double = 6.0,
    val settleSigma: Double = 0.35,
    val freezeZ: Double = 3.5,
    val minScaleFraction: Double = 0.02,
    val qualityFloor: Double = 0.35,
    val rollbackWindow: Int = 60,
    val rollbackCooldownSeconds: Double = 1800.0,
    val headMinLabels: Int = 20,
    val headMinPerClass: Int = 5,
    val headMinProspective: Int = 30,
    val headMargin: Double = 0.15,
    val headMinWinRate: Double = 0.65,
    val headLearningRate: Double = 0.30
)

data class LearningEvent(
    val kind: String,
    val atSeconds: Double,
    val detail: String,
    val fromTier: String? = null,
    val toTier: String? = null,
    val metric: String? = null
)

data class HeadStatus(
    val status: String = "collecting",
    val nTrain: Int = 0,
    val nPos: Int = 0,
    val nNeg: Int = 0,
    val nProspective: Int = 0,
    val prospectiveWins: Int = 0,
    val prospectiveLogLoss: Double? = null,
    val baselineLogLoss: Double? = null,
    val reason: String = "no wearer-labelled events recorded yet"
)

data class LearningSnapshot(
    val tier: String,
    val modelVersion: String,
    val upgrades: Int,
    val wornHours: Double,
    val observations: Int,
    val daysCovered: Int,
    val confidence: Double,
    val nextTier: String?,
    val remaining: List<String>,
    val headline: String,
    val head: HeadStatus,
    val events: List<LearningEvent>
)

/** Persistence seam so the model can be exercised without an Android Context. */
interface LearningStore {
    fun load(): String?
    fun save(json: String)
}

class SharedPreferencesLearningStore(context: Context, patientId: String) : LearningStore {
    private val prefs = context.getSharedPreferences("wearable_learning", Context.MODE_PRIVATE)
    private val key = "model_$patientId"
    override fun load(): String? = prefs.getString(key, null)
    override fun save(json: String) {
        prefs.edit().putString(key, json).apply()
    }
}

private fun median(sorted: DoubleArray): Double =
    if (sorted.isEmpty()) Double.NaN
    else if (sorted.size % 2 == 1) sorted[sorted.size / 2]
    else 0.5 * (sorted[sorted.size / 2 - 1] + sorted[sorted.size / 2])

private fun percentile(sorted: DoubleArray, p: Double): Double {
    if (sorted.isEmpty()) return Double.NaN
    val rank = p * (sorted.size - 1)
    val low = rank.toInt()
    val high = min(low + 1, sorted.size - 1)
    val weight = rank - low
    return sorted[low] * (1 - weight) + sorted[high] * weight
}

/**
 * Streaming, robust, drift-aware statistics for one metric.
 *
 * Descriptive statistics (what the samples looked like) are kept separate from the
 * personal norm (the reference the wearer is compared against). The norm is set once
 * and thereafter only moves through metered adaptation, so a genuine event cannot be
 * averaged away.
 */
class MetricLearning(private val metric: String, private val cfg: LearningConfig) {
    private val bounds = METRIC_BOUNDS[metric] ?: (Double.NEGATIVE_INFINITY..Double.POSITIVE_INFINITY)

    var n: Int = 0
        private set
    var rejected: Int = 0
        private set
    private var qualitySum = 0.0
    private var firstTs: Double? = null
    var lastTs: Double? = null
        private set
    private val days = LinkedHashSet<String>()

    private val reservoir = ArrayDeque<Double>()
    private val tail = ArrayDeque<Double>()
    private val cleanReservoir = ArrayDeque<Double>()
    private val hourBuckets = Array(24) { ArrayDeque<Double>() }

    var median: Double? = null
        private set
    var scale: Double = 0.0
        private set
    private var descMedian: Double? = null
    private var descMad: Double = 0.0
    private var descP25: Double? = null
    private var descP75: Double? = null

    var devSeconds: Double = 0.0
        private set
    var devSamples: Int = 0
        private set
    private var quietSamples = 0
    private var phSum = 0.0
    private var phMin = 0.0
    private var phNegSum = 0.0
    private var phMax = 0.0
    var phAlarm: Boolean = false
        private set
    var absorbing: Boolean = false
        private set
    private var absorbFrom: Double? = null
    var absorbedTotal: Double = 0.0
        private set
    var frozenSamples: Int = 0
        private set
    var circadianEnabled: Boolean = false

    private val daysCovered: Int get() = days.size
    val quality: Double get() = if (n == 0) 0.0 else qualitySum / n
    val normReady: Boolean get() = median != null && scale > 0.0
    val hourCoverage: Map<Int, Int>
        get() = hourBuckets.withIndex().filter { it.value.isNotEmpty() }
            .associate { it.index to it.value.size }

    fun setCircadian(enabled: Boolean) {
        circadianEnabled = enabled
    }

    fun expected(ts: Double): Double {
        val centre = median ?: (descMedian ?: 0.0)
        if (circadianEnabled) {
            val hour = hourOf(ts)
            val bucket = hourBuckets[hour]
            if (bucket.size >= 3) return centre + medianOf(ArrayDeque(bucket))
        }
        return centre
    }

    fun add(value: Double, ts: Double, quality: Double, dt: Double): Boolean {
        if (value.isNaN() || value.isInfinite()) return false
        if (value < bounds.start || value > bounds.endInclusive) {
            rejected += 1
            return false
        }
        n += 1
        qualitySum += quality.coerceIn(0.0, 1.0)
        if (firstTs == null) firstTs = ts
        lastTs = ts
        days.add(dayKey(ts))

        push(reservoir, value, cfg.reservoirSize)
        push(tail, value, cfg.recentWindow)
        if (!absorbing && devSeconds <= 0.0) {
            push(hourBuckets[hourOf(ts)], value, cfg.bucketSize)
            push(cleanReservoir, value, cfg.reservoirSize)
        }
        if (n % max(1, cfg.recalcEvery) == 1 || descMedian == null) refresh()
        detect(ts, dt)
        return true
    }

    private fun refresh() {
        if (reservoir.isEmpty()) return
        val sorted = reservoir.toDoubleArray().also { it.sort() }
        val med = median(sorted)
        descMedian = med
        descMad = median(sorted.map { abs(it - med) }.sorted().toDoubleArray())
        descP25 = percentile(sorted, 0.25)
        descP75 = percentile(sorted, 0.75)

        val span = (lastTs ?: 0.0) - (firstTs ?: 0.0)
        if (median == null && n >= cfg.normInitSamples && span >= cfg.normInitSpanSeconds &&
            quality >= cfg.normInitMinQuality
        ) {
            val madScale = max(1.4826 * descMad, cfg.minScaleFraction * abs(med))
            val iqrScale = max((descP75!! - descP25!!) / 1.349, 1e-9)
            median = med
            scale = max(madScale, iqrScale)
        }
    }

    private fun detect(ts: Double, dt: Double) {
        if (!normReady || tail.isEmpty()) return
        val r = tail.last() - expected(ts)
        val z = r / scale
        val delta = cfg.phDeltaSigma * scale
        phSum += (r - delta)
        phMin = min(phMin, phSum)
        phNegSum += (r + delta)
        phMax = max(phMax, phNegSum)
        val threshold = cfg.phLambdaSigma * scale
        phAlarm = (phSum - phMin) > threshold || (phMax - phNegSum) > threshold

        if (abs(z) >= cfg.driftWindowSigma) {
            devSeconds += max(0.0, dt)
            devSamples += 1
            quietSamples = 0
        } else if (++quietSamples >= cfg.quietResetSamples) {
            clearDeviation()
        }
    }

    private fun clearDeviation() {
        phSum = 0.0; phMin = 0.0; phNegSum = 0.0; phMax = 0.0; phAlarm = false
        devSeconds = 0.0; devSamples = 0; quietSamples = 0
    }

    fun z(value: Double?, ts: Double? = null): Double? {
        if (value == null || !normReady) return null
        if (circadianEnabled && ts != null) {
            val hour = hourOf(ts)
            if (hourBuckets[hour].size >= 3) return (value - expected(ts)) / scale
        }
        return (value - median!!) / scale
    }

    fun range(): Pair<Double, Double>? {
        val centre = median ?: return null
        if (!normReady) return null
        return (centre - 1.645 * scale) to (centre + 1.645 * scale)
    }

    fun maybeAbsorb(ts: Double, wornSinceLast: Double): Double? {
        if (!normReady || tail.isEmpty()) return null
        if (!absorbing) {
            val gap = recentMedian() - expected(ts)
            val earned = devSeconds >= cfg.driftMinPersistenceSeconds && phAlarm &&
                abs(gap) >= cfg.driftMinShiftSigma * scale
            if (!earned) return null
            absorbing = true
            absorbFrom = median
            clearDeviation()
            return gap
        }
        if (absorbFrom != null && abs(median!! - absorbFrom!!) >= cfg.maxAbsorbSigma * scale) {
            absorbing = false
            clearDeviation()
            return null
        }
        val gap = recentMedian() - expected(ts)
        if (abs(gap) <= cfg.settleSigma * scale) {
            absorbing = false
            clearDeviation()
            return null
        }
        val budget = cfg.maxAdaptSigmaPerHour * scale * max(wornSinceLast, 0.0) / 3600.0
        val step = if (gap > 0) min(abs(gap), budget) else -min(abs(gap), budget)
        median = median!! + step
        absorbedTotal += step
        clearDeviation()
        return null
    }

    fun gentleTrack(ts: Double, wornSinceLast: Double): Double? {
        if (absorbing || devSeconds > 0.0 || !normReady || tail.isEmpty()) return null
        if (quietSamples < tail.size) return null
        val r = tail.last() - expected(ts)
        if (abs(r) > cfg.freezeZ * scale) {
            frozenSamples += 1
            return null
        }
        val gap = recentMedian() - expected(ts)
        if (abs(gap) < 0.5 * scale) return null
        val budget = cfg.maxAdaptSigmaPerHour * scale * max(wornSinceLast, 0.0) / 3600.0
        val step = if (gap > 0) min(abs(gap), budget) else -min(abs(gap), budget)
        median = median!! + step
        absorbedTotal += step
        return step
    }

    private fun recentMedian(): Double =
        if (tail.isEmpty()) (median ?: 0.0) else median(ArrayDeque(tail).toDoubleArray().also { it.sort() })

    private fun hourOf(ts: Double): Int = ((ts / 3600.0).toLong() % 24).toInt().let { if (it < 0) it + 24 else it }

    private fun dayKey(ts: Double): String = (ts / 86400.0).toLong().toString()

    private fun push(deck: ArrayDeque<Double>, value: Double, limit: Int) {
        deck.addLast(value)
        while (deck.size > limit) deck.removeFirst()
    }

    private fun medianOf(deck: ArrayDeque<Double>): Double =
        median(deck.toDoubleArray().also { it.sort() })

    fun toJson(): JSONObject = JSONObject().apply {
        put("n", n); put("rejected", rejected); put("quality", quality)
        put("median", median ?: JSONObject.NULL); put("scale", scale)
        put("absorbed_total", absorbedTotal); put("frozen_samples", frozenSamples)
        put("reservoir", JSONArray(reservoir.toList()))
        put("tail", JSONArray(tail.toList()))
        put("hours", JSONObject(hourCoverage))
    }

    companion object {
        fun fromJson(metric: String, json: JSONObject, cfg: LearningConfig): MetricLearning {
            val obj = MetricLearning(metric, cfg)
            obj.n = json.optInt("n", 0)
            obj.rejected = json.optInt("rejected", 0)
            obj.qualitySum = json.optDouble("quality", 0.0) * obj.n
            if (!json.isNull("median")) obj.median = json.optDouble("median")
            obj.scale = json.optDouble("scale", 0.0)
            obj.absorbedTotal = json.optDouble("absorbed_total", 0.0)
            obj.frozenSamples = json.optInt("frozen_samples", 0)
            json.optJSONArray("reservoir")?.let { arr ->
                for (i in 0 until arr.length()) obj.push(obj.reservoir, arr.optDouble(i), cfg.reservoirSize)
            }
            json.optJSONArray("tail")?.let { arr ->
                for (i in 0 until arr.length()) obj.push(obj.tail, arr.optDouble(i), cfg.recentWindow)
            }
            obj.refresh()
            return obj
        }
    }
}

private const val HEAD_FEATURES = 6

/**
 * Online logistic regression with prospective (leak-free) validation.
 *
 * Feature set: hr_z, rmssd_z, temp_z, activity_z, hour_sin, hour_cos. The GSR
 * feature left with the GSR hardware, so the head no longer has a channel that
 * never produces a value.
 */
class SupervisedHead(private val cfg: LearningConfig) {
    var w = DoubleArray(HEAD_FEATURES)
    var b = 0.0
    var status = HeadStatus()
        private set
    private val rows = ArrayList<Pair<DoubleArray, Double>>()

    private fun sigmoid(z: Double): Double =
        if (z >= 0) 1.0 / (1.0 + exp(-z)) else exp(z) / (1.0 + exp(z))

    fun predict(x: DoubleArray): Double {
        var sum = b
        for (i in 0 until HEAD_FEATURES.coerceAtMost(x.size)) sum += w[i] * x[i]
        return sigmoid(sum)
    }

    private fun baseRate(): Double {
        val total = (status.nPos + status.nNeg).coerceAtLeast(1)
        return ((status.nPos + 1.0) / (total + 2.0)).coerceIn(1e-6, 1 - 1e-6)
    }

    fun observe(x: DoubleArray, target: Double) {
        if (status.nTrain >= cfg.headMinLabels && status.nPos >= cfg.headMinPerClass &&
            status.nNeg >= cfg.headMinPerClass
        ) {
            val p = predict(x).coerceIn(1e-9, 1 - 1e-9)
            val loss = -kotlin.math.ln(if (target >= 0.5) p else 1 - p)
            val base = baseRate()
            val baseP = if (target >= 0.5) base else 1 - base
            val baseLoss = -kotlin.math.ln(baseP.coerceIn(1e-9, 1 - 1e-9))
            val n = status.nProspective
            status = status.copy(
                prospectiveLogLoss = if (n == 0) loss else (status.prospectiveLogLoss!! * n + loss) / (n + 1),
                baselineLogLoss = if (n == 0) baseLoss else (status.baselineLogLoss!! * n + baseLoss) / (n + 1),
                prospectiveWins = status.prospectiveWins + if (loss < baseLoss) 1 else 0,
                nProspective = n + 1
            )
        }
        rows.add(x to target)
        status = status.copy(
            nTrain = status.nTrain + 1,
            nPos = status.nPos + if (target >= 0.5) 1 else 0,
            nNeg = status.nNeg + if (target < 0.5) 1 else 0
        )
        train(x, target)
        reconsider()
    }

    private fun train(x: DoubleArray, target: Double) {
        val p = predict(x)
        val prevalence = baseRate()
        val weight = if (target >= 0.5) 0.5 / prevalence else 0.5 / (1 - prevalence)
        val lr = cfg.headLearningRate / (1.0 + status.nTrain / 60.0)
        val grad = (p - target) * weight
        for (i in 0 until HEAD_FEATURES.coerceAtMost(x.size)) {
            w[i] -= lr * (grad * x[i] + 0.001 * w[i])
        }
        b -= lr * grad
    }

    private fun reconsider() {
        val canScore = status.nTrain >= cfg.headMinLabels &&
            status.nPos >= cfg.headMinPerClass && status.nNeg >= cfg.headMinPerClass
        if (!canScore) {
            status = status.copy(
                status = "collecting",
                reason = "needs ${cfg.headMinLabels} labelled events (>= ${cfg.headMinPerClass} per class); " +
                    "has ${status.nTrain} (${status.nPos} event / ${status.nNeg} normal)"
            )
            return
        }
        if (status.nProspective < cfg.headMinProspective) {
            status = status.copy(
                status = "collecting",
                reason = "scoring on unseen labels: ${status.nProspective}/${cfg.headMinProspective}"
            )
            return
        }
        val ll = status.prospectiveLogLoss ?: return
        val baseLl = status.baselineLogLoss ?: return
        val gain = if (baseLl == 0.0) 0.0 else 1.0 - ll / baseLl
        val winRate = status.prospectiveWins.toDouble() / status.nProspective
        status = if (gain >= cfg.headMargin && winRate >= cfg.headMinWinRate) {
            status.copy(
                status = "active",
                reason = "beats the base-rate predictor on ${status.nProspective} unseen labels " +
                    "(log-loss ${"%.3f".format(ll)} vs ${"%.3f".format(baseLl)}); engineering check only"
            )
        } else {
            status.copy(
                status = "withheld",
                reason = "after ${status.nProspective} unseen labels it does not clear the bar " +
                    "(log-loss ${"%.3f".format(ll)} vs base rate ${"%.3f".format(baseLl)}); " +
                    "no claim is made"
            )
        }
    }
}

/** One wearer's continually-learning model. */
class WearableLearningModel(
    val patientId: String,
    private val store: LearningStore,
    private val cfg: LearningConfig = LearningConfig()
) {
    var tier: String = "population"
        private set
    var modelVersion: String = "1.0.0"
        private set
    var wornSeconds: Double = 0.0
        private set
    var observations: Int = 0
        private set
    private var lastTs: Double? = null
    private var cooldownUntil: Double = 0.0
    private val qualityWindow = ArrayDeque<Double>()
    private val recentZ = ArrayDeque<Pair<Double, DoubleArray>>()
    private val events = ArrayList<LearningEvent>()
    private val metrics = LEARNING_METRICS.associateWith { MetricLearning(it, cfg) }
    private val head = SupervisedHead(cfg)
    private var samplesSinceSave = 0

    init {
        load()
    }

    private fun tierIndex(): Int = TIERS.indexOf(tier).coerceAtLeast(0)

    fun observe(
        values: Map<String, Double?>,
        timestampSeconds: Double,
        quality: Double?
    ): List<LearningEvent> {
        val produced = ArrayList<LearningEvent>()
        val q = (quality ?: 1.0).coerceIn(0.0, 1.0)
        val gap = if (lastTs == null) 0.0 else timestampSeconds - lastTs!!
        val wornDelta = if (gap > 0.0 && gap <= cfg.maxWornGapSeconds) gap else 0.0
        wornSeconds += wornDelta
        lastTs = timestampSeconds
        observations += 1
        push(qualityWindow, q, cfg.rollbackWindow)

        for ((metric, learner) in metrics) {
            val value = values[metric] ?: continue
            if (!learner.add(value, timestampSeconds, q, wornDelta)) continue
            if (tierIndex() >= TIERS.indexOf("adaptive")) {
                val shift = learner.maybeAbsorb(timestampSeconds, wornDelta)
                if (shift != null) {
                    val b = modelVersion.split(".").map { it.toIntOrNull() ?: 0 }
                    modelVersion = "${b[0]}.${b[1]}.${b.getOrElse(2) { 0 } + 1}"
                    produced.add(
                        LearningEvent(
                            kind = "drift",
                            atSeconds = timestampSeconds,
                            metric = metric,
                            detail = "persistent shift in $metric (${"%.2f".format(shift)}); " +
                                "absorbing it into the personal norm at the rate limit"
                        )
                    )
                } else if (!learner.absorbing) {
                    learner.gentleTrack(timestampSeconds, wornDelta)
                }
            }
        }
        recentZ.addLast(timestampSeconds to zVector(values, timestampSeconds))
        while (recentZ.size > 4096) recentZ.removeFirst()

        evaluateTier(timestampSeconds)?.let { produced.add(it) }
        pushEvents(produced)
        if (++samplesSinceSave >= cfg.saveEvery) {
            samplesSinceSave = 0
            save()
        }
        return produced
    }

    private fun pushEvents(produced: List<LearningEvent>) {
        for (event in produced) {
            events.add(event)
        }
        while (events.size > cfg.historyLimit) events.removeAt(0)
    }

    private fun evaluateTier(ts: Double): LearningEvent? {
        if (tierIndex() > 0) {
            val q = qualityWindow.average().takeIf { qualityWindow.size >= 20 }
            if (q != null && q < cfg.qualityFloor && ts >= cooldownUntil) {
                cooldownUntil = ts + cfg.rollbackCooldownSeconds
                return demote(ts, "recent signal quality fell to ${"%.2f".format(q)}")
            }
        }
        val next = TIERS.getOrNull(tierIndex() + 1) ?: return null
        if (ts < cooldownUntil || !qualifies(next)) return null
        return promote(next, ts)
    }

    private fun qualifies(next: String): Boolean = when (next) {
        "personalized" -> wornSeconds >= cfg.personalMinWornSeconds &&
            metrics.values.count { it.normReady } >= cfg.personalMinMetrics &&
            recentQuality() >= cfg.personalMinQuality
        "circadian" -> wornSeconds >= cfg.circadianMinWornSeconds &&
            daysCovered() >= cfg.circadianMinDays && coveredHours() >= cfg.circadianMinBuckets
        else -> wornSeconds >= cfg.adaptiveMinWornSeconds && daysCovered() >= cfg.adaptiveMinDays &&
            metrics.values.count { it.n >= cfg.adaptiveMinMetricSamples } >= cfg.adaptiveMinMetrics
    }

    private fun promote(next: String, ts: Double): LearningEvent {
        val previous = tier
        tier = next
        metrics.values.forEach { it.setCircadian(tierIndex() >= TIERS.indexOf("circadian")) }
        val b = modelVersion.split(".").map { it.toIntOrNull() ?: 0 }
        modelVersion = "${b[0]}.${b[1] + 1}.0"
        return LearningEvent(
            kind = "promotion",
            atSeconds = ts,
            fromTier = previous,
            toTier = next,
            detail = "model upgraded to $next (v$modelVersion) after " +
                "${"%.1f".format(wornSeconds / 3600.0)} h of wearing"
        )
    }

    private fun demote(ts: Double, reason: String): LearningEvent {
        val previous = tier
        tier = TIERS[max(0, tierIndex() - 1)]
        metrics.values.forEach { it.setCircadian(tierIndex() >= TIERS.indexOf("circadian")) }
        val b = modelVersion.split(".").map { it.toIntOrNull() ?: 0 }
        modelVersion = "${b[0]}.${b[1] + 1}.0"
        return LearningEvent(
            kind = "rollback",
            atSeconds = ts,
            fromTier = previous,
            toTier = tier,
            detail = "model rolled back to $tier: $reason"
        )
    }

    private fun recentQuality(): Double =
        if (qualityWindow.isEmpty()) 0.0 else qualityWindow.average()

    private fun daysCovered(): Int =
        metrics.values.maxOfOrNull { it.n }?.let { observations / 1440 + 1 } ?: 0

    private fun coveredHours(): Int =
        metrics.values.flatMap { it.hourCoverage.entries }
            .groupBy({ it.key }, { it.value })
            .count { (_, sizes) -> sizes.count { it >= cfg.circadianBucketMin } >= 3 }

    private fun zVector(values: Map<String, Double?>, ts: Double): DoubleArray {
        fun zOf(metric: String): Double {
            val value = values[metric] ?: return 0.0
            val z = metrics[metric]?.z(value, ts) ?: run {
                val prior = POPULATION_PRIOR[metric] ?: return 0.0
                (value - prior.first) / prior.second
            }
            return z.coerceIn(-8.0, 8.0)
        }
        val hour = (ts / 3600.0) % 24.0
        val angle = 2.0 * Math.PI * hour / 24.0
        return doubleArrayOf(
            zOf("hr_bpm"), zOf("rmssd_ms"), zOf("skin_temp_c"),
            zOf("activity_level"), kotlin.math.sin(angle), kotlin.math.cos(angle)
        )
    }

    /** Wearer-reported event. Returns false when there is no recent row to attach to. */
    fun recordLabel(target: Boolean, at: Double = lastTs ?: 0.0): Boolean {
        val row = recentZ.lastOrNull { abs(it.first - at) <= 900.0 } ?: return false
        head.observe(row.second, if (target) 1.0 else 0.0)
        pushEvents(listOf(LearningEvent("capability", at, "supervised head ${head.status.status}: ${head.status.reason}")))
        save()
        return true
    }

    fun snapshot(): LearningSnapshot {
        val next = TIERS.getOrNull(tierIndex() + 1)
        val remaining = buildList {
            if (next == "personalized") {
                if (wornSeconds < cfg.personalMinWornSeconds)
                    add("Wear the device")
                if (metrics.values.count { it.normReady } < cfg.personalMinMetrics)
                    add("Signals with a personal norm")
            } else if (next == "circadian") {
                if (wornSeconds < cfg.circadianMinWornSeconds) add("Wear the device")
                if (daysCovered() < cfg.circadianMinDays) add("Days covered")
                if (coveredHours() < cfg.circadianMinBuckets) add("Hours of day covered")
            } else if (next == "adaptive") {
                if (wornSeconds < cfg.adaptiveMinWornSeconds) add("Wear the device")
                if (daysCovered() < cfg.adaptiveMinDays) add("Days covered")
                if (metrics.values.count { it.n >= cfg.adaptiveMinMetricSamples } < cfg.adaptiveMinMetrics)
                    add("Signals with enough history")
            }
        }
        return LearningSnapshot(
            tier = tier,
            modelVersion = modelVersion,
            upgrades = events.count { it.kind == "promotion" },
            wornHours = wornSeconds / 3600.0,
            observations = observations,
            daysCovered = daysCovered(),
            confidence = confidence(),
            nextTier = next,
            remaining = remaining,
            headline = TIER_HEADLINES[tier] ?: "",
            head = head.status,
            events = events.takeLast(8).reversed()
        )
    }

    fun confidence(): Double {
        val timeTerm = min(1.0, (wornSeconds / 3600.0) / (cfg.adaptiveMinWornSeconds / 3600.0))
        val coverage = min(1.0, (metrics.values.minOfOrNull { it.n } ?: 0) /
            cfg.adaptiveMinMetricSamples.toDouble())
        val quality = if (observations == 0) 0.0 else recentQuality()
        return (0.45 * timeTerm + 0.35 * coverage + 0.20 * quality).coerceIn(0.0, 1.0)
    }

    fun save() {
        val json = JSONObject().apply {
            put("schema", LearningContract.SCHEMA)
            put("patient_id", patientId)
            put("tier", tier)
            put("model_version", modelVersion)
            put("worn_seconds", wornSeconds)
            put("observations", observations)
            put("last_ts", lastTs ?: JSONObject.NULL)
            put("head", JSONObject().apply {
                put("status", head.status.status)
                put("n_train", head.status.nTrain)
                put("n_pos", head.status.nPos)
                put("n_neg", head.status.nNeg)
            })
            put("metrics", JSONObject().apply {
                metrics.forEach { (name, learner) -> put(name, learner.toJson()) }
            })
            put("events", JSONArray(events.takeLast(50).map {
                JSONObject().apply {
                    put("kind", it.kind); put("at", it.atSeconds); put("detail", it.detail)
                    put("metric", it.metric ?: JSONObject.NULL)
                }
            }))
        }
        store.save(json.toString())
    }

    private fun load() {
        val raw = store.load() ?: return
        runCatching {
            val json = JSONObject(raw)
            if (json.optString("schema") != LearningContract.SCHEMA) return
            tier = json.optString("tier", "population").takeIf { it in TIERS } ?: "population"
            modelVersion = json.optString("model_version", "1.0.0")
            wornSeconds = json.optDouble("worn_seconds", 0.0)
            observations = json.optInt("observations", 0)
            if (!json.isNull("last_ts")) lastTs = json.optDouble("last_ts")
            metrics.values.forEach { it.setCircadian(tierIndex() >= TIERS.indexOf("circadian")) }
        }
    }

    companion object {
        private fun push(deck: ArrayDeque<Double>, value: Double, limit: Int) {
            deck.addLast(value)
            while (deck.size > limit) deck.removeFirst()
        }
    }
}
