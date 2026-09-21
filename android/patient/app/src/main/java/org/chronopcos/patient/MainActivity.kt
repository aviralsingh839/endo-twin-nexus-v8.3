package org.chronopcos.patient

import android.Manifest
import android.os.Build
import android.os.Bundle
import android.util.Base64
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.compose.*
import org.chronopcos.patient.ui.theme.EndoTwinTheme
import org.chronopcos.patient.ui.screens.PatientHomeScreen
import org.chronopcos.patient.data.database.PatientDatabase
import org.chronopcos.patient.data.repository.PatientRepository
import org.chronopcos.patient.data.wearable.WearableBleManager
import org.chronopcos.patient.data.wearable.WearableDeviceSummary
import org.json.JSONArray
import org.json.JSONObject

/**
 * ENDO-TWIN Patient V8.4
 *
 * Single-patient, offline-first research interface.
 * DEMO_DATA is deliberately separated from real measured/derived/clinical data.
 * CHRONO-PCOS is a disease-model module inside the broader ENDO-TWIN platform.
 */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            EndoTwinTheme {
                PatientApp(currentPatientId = "DEMO-001")
            }
        }
    }
}

private enum class PatientTab(val route: String, val label: String) {
    Home("home", "Home"),
    Health("health", "Health"),
    Measure("measure", "Measure"),
    Timeline("timeline", "Timeline"),
    Care("care", "Care")
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PatientApp(currentPatientId: String) {
    val navController = rememberNavController()
    val current = navController.currentBackStackEntryAsState().value?.destination

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("ENDO-TWIN", fontWeight = FontWeight.Bold)
                        Text(
                            "Personal physiological modelling",
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                },
                actions = {
                    Surface(shape = RoundedCornerShape(50), color = MaterialTheme.colorScheme.tertiaryContainer) {
                        Text(
                            "DEMO • $currentPatientId",
                            modifier = Modifier.padding(horizontal = 12.dp, vertical = 7.dp),
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onTertiaryContainer
                        )
                    }
                    Spacer(Modifier.width(12.dp))
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background)
            )
        },
        bottomBar = {
            NavigationBar(containerColor = MaterialTheme.colorScheme.surface) {
                PatientTab.entries.forEach { tab ->
                    val selected = current?.hierarchy?.any { it.route == tab.route } == true
                    NavigationBarItem(
                        selected = selected,
                        onClick = {
                            navController.navigate(tab.route) {
                                popUpTo(navController.graph.startDestinationId) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = {
                            Icon(
                                when (tab) {
                                    PatientTab.Home -> Icons.Outlined.Home
                                    PatientTab.Health -> Icons.Outlined.FavoriteBorder
                                    PatientTab.Measure -> Icons.Outlined.MonitorHeart
                                    PatientTab.Timeline -> Icons.Outlined.Timeline
                                    PatientTab.Care -> Icons.Outlined.LocationOn
                                },
                                contentDescription = tab.label
                            )
                        },
                        label = { Text(tab.label) }
                    )
                }
            }
        }
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = PatientTab.Home.route,
            modifier = Modifier.padding(padding)
        ) {
            composable("home") { PatientHomeScreen(currentPatientId) }
            composable("health") { HealthScreen(currentPatientId) }
            composable("measure") { MeasureScreen(currentPatientId) }
            composable("timeline") { TimelineScreen(currentPatientId) }
            composable("care") { CareScreen() }
        }
    }
}


private suspend fun buildPatientSyncPackage(db: PatientDatabase, patientId: String): String {
    val patient = db.patientDao().getPatient(patientId)
    val root = JSONObject()
        .put("schema_version", "android-room-2")
        .put("label", if (patient?.isDemo == true) "DEMO_DATA" else "EXPORTED_PACKAGE")
        .put("exported_at", System.currentTimeMillis() / 1000.0)

    if (patient != null) {
        root.put("patient", JSONObject()
            .put("patient_id", patient.patientId)
            .put("anonymous_id", patient.anonymousId)
            .put("display_name", patient.displayName)
            .put("age_years", patient.ageYears)
            .put("bmi", patient.bmi)
        )
    }

    val sessions = JSONArray()
    db.wearableDao().getSessions(patientId).forEach { s ->
        sessions.put(JSONObject()
            .put("session_id", s.sessionId)
            .put("patient_id", s.patientId)
            .put("source", "ANDROID_BLE")
            .put("start_at", s.startedAt / 1000.0)
            .put("end_at", s.endedAt?.div(1000.0))
            .put("sample_count", 0)
            .put("data_quality", JSONObject.NULL)
            .put("notes", "Android local wearable session")
            .put("label", if (s.isDemo) "DEMO_DATA" else "REAL")
            .put("created_at", s.startedAt / 1000.0)
            .put("study_id", JSONObject.NULL)
        )
    }
    root.put("sessions", sessions)

    val events = JSONArray()
    db.wearableDao().getEvents(patientId).forEach { e ->
        events.put(JSONObject()
            .put("event_id", e.eventId)
            .put("patient_id", e.patientId)
            .put("session_id", e.sessionId ?: JSONObject.NULL)
            .put("timestamp", e.timestamp / 1000.0)
            .put("event_type", e.eventType)
            .put("detail_json", e.detail)
            .put("label", if (e.isDemo) "DEMO_DATA" else "REAL")
        )
    }
    root.put("wearable_events", events)

    val packets = JSONArray()
    db.wearableDao().getPackets(patientId).forEach { p ->
        packets.put(JSONObject()
            .put("packet_id", p.packetId)
            .put("patient_id", p.patientId)
            .put("session_id", p.sessionId ?: JSONObject.NULL)
            .put("timestamp", p.timestamp / 1000.0)
            .put("payload_base64", p.payloadBase64)
            .put("transport", p.transport)
            .put("quality", p.quality ?: JSONObject.NULL)
            .put("label", if (p.isDemo) "DEMO_DATA" else "REAL")
        )
    }
    root.put("raw_wearable_packets", packets)

    val featureVectors = JSONArray()
    db.patientDao().getMeasurements(patientId).forEach { m ->
        featureVectors.put(JSONObject()
            .put("feature_id", m.measurementId)
            .put("patient_id", m.patientId)
            .put("session_id", JSONObject.NULL)
            .put("timestamp_s", m.timestamp / 1000.0)
            .put("data_json", JSONObject()
                .put(m.type, m.value)
                .put("unit", m.unit)
                .put("provenance", m.provenance)
                .toString())
            .put("source", "ANDROID_MEASUREMENT")
            .put("algorithm_version", JSONObject.NULL)
            .put("label", if (m.isDemo) "DEMO_DATA" else "REAL")
        )
    }
    root.put("feature_vectors", featureVectors)

    root.put("profiles", JSONArray())
    root.put("symptoms", JSONArray())
    root.put("cycles", JSONArray())
    root.put("wearable_devices", JSONArray())
    root.put("reports", JSONArray())
    root.put("doctor_notes", JSONArray())
    root.put("personal_baselines", JSONArray())
    root.put("learning_runs", JSONArray())
    root.put("research_studies", JSONArray())
    root.put("research_labels", JSONArray())
    root.put("model_results", JSONArray())
    root.put("analysis_results", JSONArray())

    root.put(
        "note",
        "Phone local export. Raw BLE payloads are preserved for board-specific decoding. "
        + "Wear/removal/reconnect events are preserved. Missing intervals are never filled."
    )
    return root.toString(2)
}
@Composable
private fun SectionTitle(title: String, subtitle: String? = null) {
    Column {
        Text(title, style = MaterialTheme.typography.titleLarge)
        subtitle?.let {
            Text(it, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun ProvenanceBadge(label: String, tone: Color = MaterialTheme.colorScheme.primaryContainer) {
    Surface(shape = RoundedCornerShape(50), color = tone) {
        Text(label, modifier = Modifier.padding(horizontal = 9.dp, vertical = 5.dp), style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun MetricCard(title: String, value: String, detail: String, provenance: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
        shape = RoundedCornerShape(20.dp)
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(title, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Spacer(Modifier.weight(1f))
                ProvenanceBadge(provenance)
            }
            Text(value, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text(detail, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun DemoBanner() {
    Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF17273A)), shape = RoundedCornerShape(18.dp)) {
        Row(
            Modifier.padding(16.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.Top
        ) {
            Icon(Icons.Default.Info, null, tint = MaterialTheme.colorScheme.primary)
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("Demonstration dataset", fontWeight = FontWeight.SemiBold)
                Text(
                    "Values on this build are illustrative DEMO_DATA, not live patient measurements. Real records retain explicit provenance and quality metadata.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
private fun HomeScreen(patientId: String) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            Column(verticalArrangement = Arrangement.spacedBy(5.dp)) {
                Text("Good to see you.", style = MaterialTheme.typography.displaySmall)
                Text(
                    "Understand your physiological patterns over time.",
                    color = MaterialTheme.colorScheme.primary,
                    style = MaterialTheme.typography.bodyLarge
                )
            }
        }
        item { DemoBanner() }
        item {
            Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer), shape = RoundedCornerShape(22.dp)) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.AutoGraph, null, modifier = Modifier.size(36.dp))
                        Spacer(Modifier.width(12.dp))
                        Column {
                            Text("Personal baseline", style = MaterialTheme.typography.titleMedium)
                            Text("Illustrative learning status • not clinical certainty", style = MaterialTheme.typography.bodySmall)
                        }
                    }
                    LinearProgressIndicator(progress = 0.72f, modifier = Modifier.fillMaxWidth().height(7.dp).clip(RoundedCornerShape(50)))
                    Text("72% illustrative completeness • DEMO_DATA", style = MaterialTheme.typography.labelSmall)
                }
            }
        }
        item { SectionTitle("Today's signals", "Examples only — provenance is DEMO_DATA in this build.") }
        item { MetricCard("Heart rate", "72 bpm", "Illustrative resting-window example", "DEMO_DATA") }
        item { MetricCard("HRV • RMSSD", "48 ms", "Derived-feature example; pulse-derived HRV is not ECG", "DEMO_DATA") }
        item { MetricCard("Skin temperature", "32.5 °C", "Illustrative skin-temperature example", "DEMO_DATA") }
        item { MetricCard("Activity", "35%", "Illustrative motion/activity index", "DEMO_DATA") }
        item {
            Card(shape = RoundedCornerShape(20.dp)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Outlined.Psychology, null, tint = MaterialTheme.colorScheme.tertiary)
                        Spacer(Modifier.width(10.dp))
                        Text("CHRONO-PCOS research module", style = MaterialTheme.typography.titleMedium)
                    }
                    Text("Disease-specific research module inside ENDO-TWIN. Model outputs are not diagnoses and clinical validation is not established.")
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        ProvenanceBadge("MODEL-INFERRED", MaterialTheme.colorScheme.tertiaryContainer)
                        ProvenanceBadge("DEMO_DATA", MaterialTheme.colorScheme.secondaryContainer)
                    }
                }
            }
        }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedButton(onClick = {}, modifier = Modifier.weight(1f)) { Text("Symptoms") }
                OutlinedButton(onClick = {}, modifier = Modifier.weight(1f)) { Text("Cycle") }
            }
        }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedButton(onClick = {}, modifier = Modifier.weight(1f)) { Text("Reports") }
                OutlinedButton(onClick = {}, modifier = Modifier.weight(1f)) { Text("Settings") }
            }
        }
        item {
            Text(
                "Research / risk-screening output — not a medical diagnosis.",
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.SemiBold
            )
        }
    }
}

@Composable
private fun HealthScreen(patientId: String) {
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        item { SectionTitle("My health", "Patient-scoped workspace • $patientId") }
        item { MetricCard("Personal baseline", "72% complete", "Illustrative learning status; no clinical certainty", "DEMO_DATA") }
        item { MetricCard("Longitudinal trend", "Stable example", "Trend logic requires enough time-series observations", "DEMO_DATA") }
        item {
            Card(shape = RoundedCornerShape(20.dp)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text("How ENDO-TWIN interprets change", style = MaterialTheme.typography.titleMedium)
                    listOf("1  Personal baseline", "2  Time series and quality", "3  Change + persistence", "4  Recovery + context").forEach {
                        Text(it, style = MaterialTheme.typography.bodyMedium)
                    }
                    Text("A signal is not automatically a disease finding. Missing or low-quality data should reduce confidence rather than be filled in.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
        item {
            Card(shape = RoundedCornerShape(20.dp)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text("Provenance legend", style = MaterialTheme.typography.titleMedium)
                    listOf("MEASURED", "DERIVED", "CLINICALLY_ENTERED", "IMAGE-DERIVED", "MODEL-INFERRED", "DEMO_DATA", "UNKNOWN").forEach {
                        ProvenanceBadge(it, MaterialTheme.colorScheme.surfaceVariant)
                    }
                    Text("Every result should keep its source classification visible. UNKNOWN is a valid state.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun MeasureScreen(patientId: String) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val ble = remember { WearableBleManager(context) }
    val db = remember { PatientDatabase.getInstance(context) }
    val repository = remember {
        PatientRepository(db.patientDao(), db.wearableDao()).also {
            it.setCurrentPatientId(patientId)
        }
    }

    var selected by remember { mutableStateOf("Overview") }
    var bleState by remember { mutableStateOf("NOT_CONNECTED") }
    var scanMessage by remember { mutableStateOf("Ready to scan for a nearby wearable.") }
    var sessionId by remember { mutableStateOf<String?>(null) }
    var packetCount by remember { mutableStateOf(0) }
    val devices = remember { mutableStateListOf<WearableDeviceSummary>() }

    val exportLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument("application/json")
    ) { uri ->
        if (uri != null) {
            scope.launch {
                runCatching {
                    val json = buildPatientSyncPackage(db, patientId)
                    context.contentResolver.openOutputStream(uri)?.use { output ->
                        output.write(json.toByteArray(Charsets.UTF_8))
                    } ?: error("Could not open export destination.")
                }.onSuccess {
                    scanMessage = "Complete patient package exported locally for Doctor import."
                }.onFailure {
                    scanMessage = "Export failed: " + it.message
                }
            }
        }
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) {
        scanMessage = if (ble.missingPermissions().isEmpty()) {
            "Bluetooth permission granted. Tap Scan again."
        } else {
            "Bluetooth permission was not granted."
        }
    }

    DisposableEffect(Unit) {
        onDispose {
            ble.stopScan()
            ble.disconnect()
        }
    }

    fun scan() {
        val missing = ble.missingPermissions()
        if (missing.isNotEmpty()) {
            permissionLauncher.launch(missing)
            return
        }
        devices.clear()
        scanMessage = "Scanning for BLE devices…"
        ble.startScan(
            onDevice = { device ->
                if (devices.none { it.address == device.address }) {
                    devices.add(device)
                }
            },
            onError = { scanMessage = it }
        )
    }

    fun startEpisode(device: WearableDeviceSummary) {
        scope.launch {
            sessionId = repository.startWearSession(device.address, "BLE", false)
            packetCount = 0
            bleState = "WORN • SESSION ACTIVE"
            scanMessage = "Wear episode started for " + device.name + "."
        }
    }

    fun connect(device: WearableDeviceSummary) {
        ble.connect(
            device.address,
            onState = { state -> bleState = state },
            onBytes = { bytes ->
                val active = sessionId
                if (active != null && bytes.isNotEmpty()) {
                    scope.launch {
                        repository.recordWearablePacket(
                            active,
                            Base64.encodeToString(bytes, Base64.NO_WRAP),
                            "BLE",
                            null,
                            false
                        )
                        packetCount += 1
                    }
                }
            }
        )
    }

    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item { SectionTitle("Measurements", "Wearable connection + local acquisition • $patientId") }

        item {
            Card(
                shape = MaterialTheme.shapes.large,
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
            ) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.Bluetooth, null, tint = MaterialTheme.colorScheme.primary)
                        Spacer(Modifier.width(10.dp))
                        Column {
                            Text("Wearable connection", style = MaterialTheme.typography.titleLarge)
                            Text(
                                bleState,
                                color = MaterialTheme.colorScheme.secondary,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                    Text("The phone stores raw BLE packets locally. Sensor decoding is kept separate until the exact board firmware packet specification is fixed.")
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(onClick = { scan() }) {
                            Icon(Icons.Default.Search, null)
                            Spacer(Modifier.width(6.dp))
                            Text("Scan")
                        }
                        OutlinedButton(onClick = {
                            ble.stopScan()
                            ble.disconnect()
                            bleState = "DISCONNECTED"
                        }) {
                            Text("Disconnect")
                        }
                        OutlinedButton(onClick = {
                            exportLauncher.launch("endo_twin_" + patientId + "_sync.json")
                        }) {
                            Text("Export to doctor")
                        }
                    }
                    Text(scanMessage, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }

        if (devices.isNotEmpty()) {
            item { Text("Nearby devices", style = MaterialTheme.typography.titleMedium) }
            items(devices) { device ->
                Card(shape = MaterialTheme.shapes.medium) {
                    Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Outlined.Watch, null, tint = MaterialTheme.colorScheme.tertiary)
                        Spacer(Modifier.width(10.dp))
                        Column(Modifier.weight(1f)) {
                            Text(device.name, style = MaterialTheme.typography.titleMedium)
                            Text(device.address, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        if (sessionId == null) {
                            Button(onClick = { startEpisode(device) }) { Text("Start wear") }
                        }
                        OutlinedButton(onClick = { connect(device) }) { Text("Connect") }
                    }
                }
            }
        }

        item {
            Card(shape = MaterialTheme.shapes.medium) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Wear lifecycle", style = MaterialTheme.typography.titleMedium)
                    Text("Current session: " + (sessionId?.take(12) ?: "none"))
                    Text("Raw packets stored locally: " + packetCount)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(
                            enabled = sessionId != null,
                            onClick = {
                                scope.launch {
                                    val active = sessionId ?: return@launch
                                    repository.recordWearableEvent(
                                        active,
                                        "WEARABLE_REMOVED_BATHING",
                                        "Device removed before bathing; interval remains an explicit missing-data gap.",
                                        false
                                    )
                                    repository.endWearSession(active, "REMOVED_FOR_BATHING")
                                    sessionId = null
                                    ble.disconnect()
                                    bleState = "REMOVED • BATHING GAP RECORDED"
                                    scanMessage = "No measurements are created while the wearable is removed."
                                }
                            }
                        ) { Text("Remove for bathing") }

                        OutlinedButton(
                            enabled = sessionId == null && devices.isNotEmpty(),
                            onClick = { startEpisode(devices.first()) }
                        ) { Text("New episode") }
                    }
                }
            }
        }

        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("Overview", "Signals", "Quality", "Models", "VoxVasc").forEach { filter ->
                    FilterChip(selected = selected == filter, onClick = { selected = filter }, label = { Text(filter) })
                }
            }
        }

        when (selected) {
            "Overview" -> {
                item { MetricCard("BLE", bleState, "Transport state", "LOCAL") }
                item { MetricCard("Raw packets", packetCount.toString(), "Stored on device", "LOCAL") }
                item { MetricCard("Sensor decoding", "Pending", "Exact wearable packet contract is required before displaying physiological values.", "UNKNOWN") }
            }
            "Signals" -> item {
                Card(shape = MaterialTheme.shapes.medium) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("Signal pipeline", style = MaterialTheme.typography.titleMedium)
                        Text("Wearable → BLE → raw packet → validation → timestamp → local storage → board-specific decoder → QC → features → personal twin → research modules")
                        Text("Bathing removals are explicit lifecycle events; missing intervals are never filled with synthetic observations.")
                    }
                }
            }
            "Quality" -> item {
                Card(shape = MaterialTheme.shapes.medium) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("Acquisition quality", style = MaterialTheme.typography.titleMedium)
                        Text("Connection: " + bleState)
                        Text("Stored raw packets: " + packetCount)
                        Text("Per-channel physiological quality appears only after valid decoding.")
                    }
                }
            }
            "Models" -> item {
                Card(shape = MaterialTheme.shapes.medium) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("ENDO-TWIN research layers", style = MaterialTheme.typography.titleMedium)
                        Text("Raw observations, derived features, personal adaptation and disease-module inference remain separate.")
                        ProvenanceBadge("MODEL-INFERRED", MaterialTheme.colorScheme.tertiaryContainer)
                    }
                }
            }
            "VoxVasc" -> item {
                Card(shape = MaterialTheme.shapes.medium) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("VoxVasc", style = MaterialTheme.typography.titleMedium)
                        ProvenanceBadge("EXPERIMENTAL", MaterialTheme.colorScheme.tertiaryContainer)
                        Text("Optional voice-acoustic research modality. It remains unavailable until a valid recording is acquired.")
                    }
                }
            }
        }

        item {
            Text(
                "Research / risk-screening output — not a medical diagnosis.",
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

@Composable
private fun TimelineScreen(patientId: String) {
    val events = listOf(
        "Sensor session" to "DEMO_DATA • illustrative session • 19 Sep 2026",
        "Symptom entry" to "CLINICALLY_ENTERED • example user entry • 18 Sep 2026",
        "Cycle event" to "CLINICALLY_ENTERED • example event • 15 Sep 2026",
        "Ultrasound study" to "IMAGE-DERIVED • unsupported anatomical features remain UNKNOWN",
        "Model run" to "MODEL-INFERRED • research output • not diagnosis",
        "Report" to "Report generated • provenance retained"
    )
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { SectionTitle("Health timeline", "Chronological, patient-scoped • $patientId") }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                AssistChip(onClick = {}, label = { Text("All events") }, leadingIcon = { Icon(Icons.Default.FilterList, null) })
                AssistChip(onClick = {}, label = { Text("2026") })
            }
        }
        items(events) { (title, detail) ->
            Card(shape = RoundedCornerShape(18.dp)) {
                Row(Modifier.padding(16.dp), verticalAlignment = Alignment.Top) {
                    Box(Modifier.size(12.dp).clip(RoundedCornerShape(50)).background(MaterialTheme.colorScheme.primary))
                    Spacer(Modifier.width(14.dp))
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text(title, style = MaterialTheme.typography.titleMedium)
                        Text(detail, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
        }
    }
}

@Composable
private fun CareScreen() {
    val providers = listOf(
        "Demo Women's Health Clinic" to "DEMO DIRECTORY • Gynecology • distance illustrative 1.2 km",
        "Demo Diagnostic Centre" to "DEMO DIRECTORY • Laboratory • distance illustrative 2.1 km",
        "Demo Supplies Provider" to "DEMO DIRECTORY • Health supplies • availability not verified"
    )
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        item { SectionTitle("Find care", "Accessibility layer • real-world availability is not represented") }
        item { DemoBanner() }
        items(providers) { (name, detail) ->
            Card(shape = RoundedCornerShape(20.dp)) {
                Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Outlined.LocationOn, null, tint = MaterialTheme.colorScheme.primary)
                    Spacer(Modifier.width(12.dp))
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text(name, style = MaterialTheme.typography.titleMedium)
                        Text(detail, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    TextButton(onClick = {}) { Text("View") }
                }
            }
        }
        item {
            Text("Demo directory only • do not treat provider names, distance, hours, verification, or availability as live information.", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.error)
        }
    }
}
