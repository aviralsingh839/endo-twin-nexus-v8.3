@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)

package org.chronopcos.patient

import android.os.Bundle
import android.content.Intent
import android.content.Context
import androidx.core.content.ContextCompat
import androidx.room.Room
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.compose.setContent
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.compose.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID
import org.chronopcos.patient.ui.theme.EndoTwinTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { EndoTwinTheme { PatientApp("PUBLIC-PARTICIPANT", "Participant") } }
    }
}

private enum class PatientTab(val route: String, val label: String) {
    Home("home", "Home"),
    Health("health", "Health"),
    Measure("measure", "Measure"),
    Timeline("timeline", "3-Day Study"),
    Connect("connect", "Connect")
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun PatientApp(currentPatientId: String, alias: String) {
    val nav = rememberNavController()
    val current = nav.currentBackStackEntryAsState().value?.destination
    val tabs = PatientTab.entries

    BoxWithConstraints(Modifier.fillMaxSize()) {
        val wide = maxWidth >= 700.dp
        Scaffold(
            containerColor = MaterialTheme.colorScheme.background,
            topBar = {
                TopAppBar(
                    title = {
                        Column(verticalArrangement = Arrangement.spacedBy(1.dp)) {
                            Text("ENDO-TWIN NEXUS", fontWeight = FontWeight.ExtraBold)
                            Text("Personalized physiological modelling", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    },
                    actions = {
                        Surface(shape = RoundedCornerShape(10.dp), color = MaterialTheme.colorScheme.surfaceVariant) {
                            Text("PUBLIC TEST • $currentPatientId", Modifier.padding(horizontal = 9.dp, vertical = 7.dp), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurface, fontWeight = FontWeight.Bold)
                        }
                        Spacer(Modifier.width(12.dp))
                    },
                    colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFF142B3A), titleContentColor = Color.White)
                )
            },
            bottomBar = {
                if (!wide) {
                    NavigationBar(containerColor = MaterialTheme.colorScheme.surface) {
                        tabs.forEach { tab ->
                            val selected = current?.hierarchy?.any { it.route == tab.route } == true
                            NavigationBarItem(
                                selected = selected,
                                onClick = { nav.navigate(tab.route) { popUpTo(nav.graph.startDestinationId) { saveState = true }; launchSingleTop = true; restoreState = true } },
                                icon = { Icon(tabIcon(tab), null) },
                                label = { Text(tab.label) }
                            )
                        }
                    }
                }
            }
        ) { padding ->
            Row(Modifier.fillMaxSize().padding(padding)) {
                if (wide) {
                    NavigationRail(
                        containerColor = MaterialTheme.colorScheme.surface,
                        header = { Avatar("M", alias) }
                    ) {
                        tabs.forEach { tab ->
                            val selected = current?.hierarchy?.any { it.route == tab.route } == true
                            NavigationRailItem(
                                selected = selected,
                                onClick = { nav.navigate(tab.route) { popUpTo(nav.graph.startDestinationId) { saveState = true }; launchSingleTop = true; restoreState = true } },
                                icon = { Icon(tabIcon(tab), tab.label) },
                                label = { Text(tab.label, fontSize = 9.sp) }
                            )
                        }
                    }
                }
                NavHost(navController = nav, startDestination = PatientTab.Home.route, modifier = Modifier.weight(1f)) {
                    composable("home") { HomeScreen(currentPatientId, alias) }
                    composable("health") { HealthScreen(currentPatientId) }
                    composable("measure") { MeasureScreen(currentPatientId) }
                    composable("timeline") { PublicStudyScreen() }
                    composable("connect") { ConnectionScreen() }
                }
            }
        }
    }
}

private fun tabIcon(tab: PatientTab) = when (tab) {
    PatientTab.Home -> Icons.Outlined.Home
    PatientTab.Health -> Icons.Outlined.FavoriteBorder
    PatientTab.Measure -> Icons.Outlined.MonitorHeart
    PatientTab.Timeline -> Icons.Outlined.Timeline
    PatientTab.Connect -> Icons.Outlined.Link
}

@Composable
private fun Avatar(initial: String, label: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Box(Modifier.size(48.dp).clip(CircleShape).background(MaterialTheme.colorScheme.primary), contentAlignment = Alignment.Center) {
            Icon(Icons.Outlined.Face, label, tint = Color.White, modifier = Modifier.size(28.dp))
        }
        Text(label, style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun PageTitle(title: String, subtitle: String) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(title, style = MaterialTheme.typography.headlineSmall)
        Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun ProvenanceBadge(label: String, kind: String = "neutral") {
    val (bg, fg) = when (kind) {
        "measured" -> MaterialTheme.colorScheme.primaryContainer to MaterialTheme.colorScheme.primary
        "derived" -> MaterialTheme.colorScheme.tertiaryContainer to MaterialTheme.colorScheme.tertiary
        "warn" -> MaterialTheme.colorScheme.secondaryContainer to MaterialTheme.colorScheme.secondary
        "error" -> MaterialTheme.colorScheme.errorContainer to MaterialTheme.colorScheme.error
        else -> MaterialTheme.colorScheme.surfaceVariant to MaterialTheme.colorScheme.onSurfaceVariant
    }
    Surface(shape = RoundedCornerShape(8.dp), color = bg) {
        Text(label, Modifier.padding(horizontal = 8.dp, vertical = 5.dp), style = MaterialTheme.typography.labelSmall, color = fg, fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun MiniTrend(values: List<Float>, modifier: Modifier = Modifier, line: Color = MaterialTheme.colorScheme.primary) {
    Canvas(modifier.height(72.dp).fillMaxWidth()) {
        if (values.size < 2) return@Canvas
        val min = values.minOrNull() ?: return@Canvas
        val max = values.maxOrNull() ?: return@Canvas
        val span = (max - min).coerceAtLeast(0.001f)
        val path = Path()
        values.forEachIndexed { index, value ->
            val x = size.width * index / values.lastIndex.coerceAtLeast(1)
            val y = size.height - (value - min) / span * size.height
            if (index == 0) path.moveTo(x, y) else path.lineTo(x, y)
        }
        drawLine(MaterialTheme.colorScheme.outline, Offset(0f, size.height * .5f), Offset(size.width, size.height * .5f), 1f)
        drawPath(path, color = line, style = Stroke(width = 3f, cap = StrokeCap.Round))
    }
}

@Composable
private fun MetricCard(title: String, value: String, detail: String, provenance: String, trend: List<Float> = emptyList()) {
    Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(12.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface), border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outline)) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(title, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Spacer(Modifier.weight(1f))
                ProvenanceBadge(provenance, if (provenance == "MEASURED") "measured" else if (provenance == "DERIVED") "derived" else "neutral")
            }
            Text(value, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.ExtraBold)
            Text(detail, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            if (trend.size > 1) MiniTrend(trend)
        }
    }
}

@Composable
private fun DemoBanner() {
    Card(shape = RoundedCornerShape(16.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Row(Modifier.padding(14.dp), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.Top) {
            Box(Modifier.size(34.dp).clip(RoundedCornerShape(10.dp)).background(MaterialTheme.colorScheme.primaryContainer), contentAlignment = Alignment.Center) {
                Icon(Icons.Outlined.Info, null, tint = MaterialTheme.colorScheme.primary)
            }
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("Demonstration dataset", fontWeight = FontWeight.Bold)
                Text("Synthetic values are illustrative and remain DEMO_DATA; they are not live clinical measurements.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}

@Composable
private fun HomeScreen(patientId: String, alias: String) {
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        item { PageTitle("Public Test Workspace", "Anonymous participant • $patientId") }
        item {
            Card(shape = RoundedCornerShape(12.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer), border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outline)) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("3-day wearable observation", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                    Text("The participant wears the ESP32-S3 pod during ordinary daily life. The app records timestamped CP2 packets locally and keeps the participant de-identified.")
                    ProvenanceBadge("REAL ACQUISITION ONLY", "measured")
                }
            }
        }
        item {
            SectionTitle("What happens next", "No synthetic values are shown in the public-test workflow.")
            listOf(
                "Start the 3-day study and keep the phone connected to ENDO-TWIN-S3.",
                "A persistent notification shows that recording is active.",
                "The app records raw CP2 packets locally and reconnects after temporary Wi-Fi loss.",
                "After Day 3, export the study and run baseline/longitudinal analysis on the desktop."
            ).forEachIndexed { i, text ->
                Card(shape = RoundedCornerShape(14.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                    Row(Modifier.padding(14.dp), verticalAlignment = Alignment.Top) {
                        Text((i + 1).toString(), fontWeight = FontWeight.ExtraBold)
                        Spacer(Modifier.width(12.dp))
                        Text(text)
                    }
                }
            }
        }
        item {
            Card(shape = RoundedCornerShape(12.dp), border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outline)) {
                Column(Modifier.padding(15.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("Research boundary", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Text("The wearable can provide physiological signals and data-quality information. It does not establish a diagnosis. Three days are an engineering/public-test window, not clinical validation.")
                }
            }
        }
    }
}

@Composable
private fun HealthScreen(patientId: String) {
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        item { PageTitle("Health", "Personal baseline and longitudinal context • $patientId") }
        item {
            Card(shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Baseline status", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                    Text("Waiting for the three-day observation window. The baseline is calculated from collected observations rather than a fixed population reference.")
                    ProvenanceBadge("BASELINE: NOT READY", "warn")
                }
            }
        }
        item {
            SectionTitle("Interpretation order", "The system should evaluate these in sequence.")
            listOf(
                "Acquisition coverage",
                "Sensor/packet quality",
                "Feature extraction",
                "Personal baseline",
                "Repeated change across time",
                "Research-model interpretation"
            ).forEachIndexed { i, text ->
                Row(Modifier.fillMaxWidth().padding(vertical = 5.dp), verticalAlignment = Alignment.CenterVertically) {
                    Box(Modifier.size(26.dp).clip(CircleShape).background(MaterialTheme.colorScheme.primaryContainer), contentAlignment = Alignment.Center) {
                        Text((i + 1).toString(), color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                    }
                    Spacer(Modifier.width(10.dp))
                    Text(text)
                }
            }
        }
        item { Text("No diagnosis is produced by this screen.", color = MaterialTheme.colorScheme.error, fontWeight = FontWeight.Bold) }
    }
}

@Composable
private fun MeasureScreen(patientId: String) {
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        item { PageTitle("Acquisition", "Live engineering status • $patientId") }
        item {
            Card(shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                    Text("Recorded channels", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                    listOf(
                        "MAX30102" to "IR / red PPG",
                        "MPU6050" to "acceleration / gyro",
                        "GSR" to "finger-electrode analog channel",
                        "BME280" to "temperature / humidity / pressure",
                        "BH1750" to "ambient light"
                    ).forEach { (name, detail) ->
                        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                            Text(name, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                            Text(detail, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }
            }
        }
        item {
            Card(shape = RoundedCornerShape(16.dp)) {
                Column(Modifier.padding(15.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
                    Text("Quality gates", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Text("CRC validation → packet freshness → channel quality → artifact handling → feature extraction.")
                    ProvenanceBadge("MEASURED → DERIVED", "derived")
                    Text("A high packet count does not mean high physiological validity. Contact, motion, light, electrode placement and environmental conditions can affect the signals.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
}

@Composable
private fun PublicStudyScreen() {
    val context = androidx.compose.ui.platform.LocalContext.current
    val scope = rememberCoroutineScope()
    val db = remember {
        Room.databaseBuilder(context, org.chronopcos.patient.data.database.PatientDatabase::class.java, "endo_twin_patient.db")
            .addMigrations(org.chronopcos.patient.data.database.MIGRATION_2_3).build()
    }
    val prefs = remember { context.getSharedPreferences("public_study", Context.MODE_PRIVATE) }
    var consent by remember { mutableStateOf(prefs.getBoolean("consent", false)) }
    var participantId by remember { mutableStateOf(prefs.getString("participant_id", "") ?: "") }
    var studyId by remember { mutableStateOf(prefs.getString("study_id", "") ?: "") }
    var startedAt by remember { mutableStateOf(prefs.getLong("started_at", 0L)) }
    var plannedEnd by remember { mutableStateOf(prefs.getLong("planned_end", 0L)) }
    var status by remember { mutableStateOf(prefs.getString("status", "READY") ?: "READY") }
    var dayCounts by remember { mutableStateOf(listOf(0, 0, 0)) }
    var validCounts by remember { mutableStateOf(listOf(0, 0, 0)) }
    val exportLauncher = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("text/csv")) { uri ->
        if (uri != null && participantId.isNotBlank()) {
            scope.launch(Dispatchers.IO) {
                val packets = db.patientDao().getRawPackets(participantId)
                context.contentResolver.openOutputStream(uri)?.bufferedWriter()?.use { out ->
                    out.appendLine("received_at_ms,transport,crc_valid,payload")
                    packets.asReversed().forEach { p ->
                        val payload = p.payload.replace("\"", "\"\"")
                        out.appendLine(p.receivedAt.toString() + "," + p.transport + "," + p.crcValid + ",\"" + payload + "\"")
                    }
                }
            }
        }
    }

    fun refresh() {
        if (startedAt <= 0L || participantId.isBlank()) return
        scope.launch {
            val counts = mutableListOf<Int>()
            val valids = mutableListOf<Int>()
            for (day in 0..2) {
                val from = startedAt + day * 86_400_000L
                val to = minOf(System.currentTimeMillis(), from + 86_400_000L)
                counts += db.patientDao().countRawPackets(participantId, from, to)
                valids += db.patientDao().countValidPackets(participantId, from, to)
            }
            dayCounts = counts
            validCounts = valids
        }
    }

    DisposableEffect(Unit) { onDispose { db.close() } }
    LaunchedEffect(startedAt, status) { refresh() }

    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        item { PageTitle("3-Day Public Test", "Anonymous wearable study • local-only recording") }

        item {
            Card(shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text("Before starting", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                    Text("Use only a participant code. Do not enter a name, phone number, address, email, diagnosis, or other identifying information. Raw CP2 packets stay in this app's local Room database.")
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(checked = consent, onCheckedChange = {
                            consent = it
                            prefs.edit().putBoolean("consent", it).apply()
                        })
                        Text("Participant has been informed and agrees to this 3-day research prototype recording.")
                    }
                    Text("This is not a medical device or diagnostic test.", color = MaterialTheme.colorScheme.error, fontWeight = FontWeight.Bold)
                }
            }
        }

        item {
            Card(shape = RoundedCornerShape(18.dp)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Study status", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Text("Participant: " + if (participantId.isBlank()) "not assigned" else participantId)
                    Text("Status: " + status)
                    if (startedAt > 0L) {
                        val elapsed = ((System.currentTimeMillis() - startedAt).coerceAtLeast(0L) / 86_400_000L).coerceAtMost(2L) + 1L
                        Text("Day " + elapsed + " of 3 • planned end " + java.text.SimpleDateFormat("dd MMM HH:mm", java.util.Locale.getDefault()).format(java.util.Date(plannedEnd)))
                    }
                }
            }
        }

        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                Button(
                    onClick = {
                        val pid = "PUBLIC-" + UUID.randomUUID().toString().replace("-", "").take(8).uppercase()
                        val sid = "STUDY-" + UUID.randomUUID().toString().replace("-", "").take(8).uppercase()
                        val start = System.currentTimeMillis()
                        val end = start + 3L * 86_400_000L
                        participantId = pid; studyId = sid; startedAt = start; plannedEnd = end; status = "ACTIVE"
                        prefs.edit().putString("participant_id", pid).putString("study_id", sid).putLong("started_at", start).putLong("planned_end", end).putString("status", "ACTIVE").apply()
                        scope.launch {
                            db.patientDao().insertPublicStudy(org.chronopcos.patient.data.database.PublicStudyEntity(sid, pid, start, end, null, true, "ACTIVE"))
                        }
                        val intent = Intent(context, org.chronopcos.patient.study.PublicStudyService::class.java).apply {
                            putExtra(org.chronopcos.patient.study.PublicStudyService.EXTRA_HOST, "192.168.4.1")
                            putExtra(org.chronopcos.patient.study.PublicStudyService.EXTRA_PORT, 7777)
                            putExtra(org.chronopcos.patient.study.PublicStudyService.EXTRA_PATIENT_ID, pid)
                            putExtra(org.chronopcos.patient.study.PublicStudyService.EXTRA_STUDY_ID, sid)
                        }
                        ContextCompat.startForegroundService(context, intent)
                    },
                    enabled = consent && status != "ACTIVE",
                    modifier = Modifier.weight(1f)
                ) { Text("Start 3-Day Test") }

                OutlinedButton(
                    onClick = { exportLauncher.launch((if (studyId.isBlank()) "endo_twin_public_3day" else studyId) + ".csv") },
                    enabled = participantId.isNotBlank(),
                    modifier = Modifier.weight(1f)
                ) { Text("Export CSV") }

                OutlinedButton(
                    onClick = {
                        context.stopService(Intent(context, org.chronopcos.patient.study.PublicStudyService::class.java))
                        status = "STOPPED"
                        prefs.edit().putString("status", "STOPPED").apply()
                    },
                    enabled = status == "ACTIVE",
                    modifier = Modifier.weight(1f)
                ) { Text("Stop") }
            }
        }

        item { Text("Timeline", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold) }

        items((0..2).toList()) { day ->
            val total = dayCounts.getOrElse(day) { 0 }
            val valid = validCounts.getOrElse(day) { 0 }
            val quality = if (total > 0) valid.toFloat() / total else 0f
            Card(shape = RoundedCornerShape(16.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                Column(Modifier.padding(15.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("DAY " + (day + 1), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        Spacer(Modifier.weight(1f))
                        ProvenanceBadge(if (total > 0) "RECORDED" else "WAITING", if (total > 0) "measured" else "neutral")
                    }
                    Text(total.toString() + " CP2 packets • " + valid.toString() + " CRC-valid")
                    LinearProgressIndicator(progress = { quality }, Modifier.fillMaxWidth())
                    Text(
                        if (total == 0) "No recorded packets yet."
                        else "Packet integrity " + String.format("%.1f%%", quality * 100f) + ". This is acquisition quality, not physiological validity.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }

        item {
            Card(shape = RoundedCornerShape(16.dp)) {
                Column(Modifier.padding(15.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("After Day 3", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Text("Export the recorded data to the desktop ENDO-TWIN pipeline. The desktop baseline engine should then calculate personal reference statistics from the collected observations. Three calendar days make the baseline eligible for the project's minimum longitudinal coverage, but do not by themselves establish clinical validity.")
                }
            }
        }
    }
}
 
@Composable
private fun ConnectionScreen() {
    val context = androidx.compose.ui.platform.LocalContext.current
    val client = remember { org.chronopcos.patient.wifi.EndoTwinTcpClient(context) }
    var state by remember { mutableStateOf(client.state) }
    var endpoint by remember { mutableStateOf("192.168.4.1") }
    var portText by remember { mutableStateOf("7777") }
    var device by remember { mutableStateOf<String?>(null) }
    var packets by remember { mutableStateOf(0) }
    var latest by remember { mutableStateOf("Waiting for a live CP2 frame…") }
    var error by remember { mutableStateOf<String?>(null) }

    DisposableEffect(client) {
        client.onState = { state = it }
        client.onDevice = { device = it }
        client.onError = { error = it }
        client.onSample = { sample ->
            packets += 1
            latest = "IR ${sample.ir} • Red ${sample.red} • GSR ${sample.gsr} • Temp ${sample.temp0 ?: Double.NaN} • status ${sample.status}"
        }
        onDispose { client.disconnect() }
    }

    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(13.dp)) {
        item { PageTitle("ESP8266 Wearable", "LIVE Wi-Fi/TCP • ENDO-TWIN-ESP8266") }
        item {
            Card(shape = RoundedCornerShape(16.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                Column(Modifier.padding(15.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                    OutlinedTextField(endpoint, { endpoint = it }, label = { Text("ESP32-S3 IP / host") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(portText, { portText = it }, label = { Text("TCP port") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    Text("${state.name} • ${device ?: "Not connected"}", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.ExtraBold)
                    Text("CP2 packets received: $packets")
                    Text(latest, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
                }
            }
        }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                Button(onClick = { client.connect(endpoint, portText.toIntOrNull() ?: 7777); error = null }, Modifier.weight(1f)) { Text("Connect ESP32-S3") }
                OutlinedButton(onClick = { client.disconnect() }, Modifier.weight(1f)) { Text("Disconnect") }
            }
        }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                OutlinedButton(onClick = { client.ping() }, Modifier.weight(1f), enabled = state == org.chronopcos.patient.wifi.EndoTwinTcpClient.State.CONNECTED) { Text("PING") }
                OutlinedButton(onClick = { client.whoAmI() }, Modifier.weight(1f), enabled = state == org.chronopcos.patient.wifi.EndoTwinTcpClient.State.CONNECTED) { Text("WHOAMI") }
            }
        }
        item { Text("The ESP32-S3 wearable uses Wi-Fi/TCP on port 7777. CP2 frames are CRC-validated before storage.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) }
    }
}

private fun endpointFor(raw: String, path: String): String {
    val v = raw.trim().trimEnd('/')
    val base = if (v.startsWith("http://") || v.startsWith("https://")) v else "http://$v"
    return base + path
}

private suspend fun getJson(url: String): String = withContext(Dispatchers.IO) {
    val c = (URL(url).openConnection() as HttpURLConnection).apply {
        requestMethod = "GET"
        connectTimeout = 5000
        readTimeout = 5000
        useCaches = false
    }
    try {
        val r = c.responseCode
        val s = if (r in 200..299) c.inputStream else c.errorStream
        val b = s?.bufferedReader()?.use { it.readText() }.orEmpty()
        if (r !in 200..299) error("HTTP $r: $b")
        b
    } finally { c.disconnect() }
}

private suspend fun postJson(url: String, body: String, token: String? = null): String = withContext(Dispatchers.IO) {
    val c = (URL(url).openConnection() as HttpURLConnection).apply {
        requestMethod = "POST"
        connectTimeout = 5000
        readTimeout = 5000
        doOutput = true
        useCaches = false
        setRequestProperty("Content-Type", "application/json")
        token?.let { setRequestProperty("X-Endo-Token", it) }
    }
    try {
        c.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
        val r = c.responseCode
        val s = if (r in 200..299) c.inputStream else c.errorStream
        val b = s?.bufferedReader()?.use { it.readText() }.orEmpty()
        if (r !in 200..299) error("HTTP $r: $b")
        b
    } finally { c.disconnect() }
}
