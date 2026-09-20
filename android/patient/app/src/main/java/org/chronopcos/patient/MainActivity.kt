package org.chronopcos.patient

import android.os.Bundle
import androidx.activity.ComponentActivity
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
import org.chronopcos.patient.ui.theme.EndoTwinTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { EndoTwinTheme { PatientApp("DEMO-001", "Mira") } }
    }
}

private enum class PatientTab(val route: String, val label: String) {
    Home("home", "Home"),
    Health("health", "Health"),
    Measure("measure", "Measure"),
    Timeline("timeline", "Timeline"),
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
                            Text("Personalized physiological modelling", style = MaterialTheme.typography.labelSmall, color = Color(0xFFDDE5FA))
                        }
                    },
                    actions = {
                        Surface(shape = RoundedCornerShape(10.dp), color = Color(0xFF33405A)) {
                            Text("DEMO_DATA • $currentPatientId", Modifier.padding(horizontal = 9.dp, vertical = 7.dp), style = MaterialTheme.typography.labelSmall, color = Color(0xFFDDE3FF), fontWeight = FontWeight.Bold)
                        }
                        Spacer(Modifier.width(12.dp))
                    },
                    colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFF5A678B), titleContentColor = Color.White)
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
                    composable("timeline") { TimelineScreen(currentPatientId) }
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
        Box(Modifier.size(48.dp).clip(CircleShape).background(Color(0xFF8F9CE9)), contentAlignment = Alignment.Center) {
            Icon(Icons.Outlined.Face, label, tint = Color.White, modifier = Modifier.size(28.dp))
        }
        Text(label, style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun PageTitle(title: String, subtitle: String) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(title, style = MaterialTheme.typography.displaySmall)
        Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun ProvenanceBadge(label: String, kind: String = "neutral") {
    val (bg, fg) = when (kind) {
        "measured" -> Color(0xFF193F39) to Color(0xFF77D8BE)
        "derived" -> Color(0xFF39345A) to Color(0xFFB8AEFF)
        "warn" -> Color(0xFF4E3C20) to Color(0xFFF1B969)
        "error" -> Color(0xFF4D2B2C) to Color(0xFFFF9C90)
        else -> Color(0xFF2A303D) to Color(0xFFBCC5D5)
    }
    Surface(shape = RoundedCornerShape(8.dp), color = bg) {
        Text(label, Modifier.padding(horizontal = 8.dp, vertical = 5.dp), style = MaterialTheme.typography.labelSmall, color = fg, fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun MiniTrend(values: List<Float>, modifier: Modifier = Modifier, line: Color = Color(0xFF63D8C3)) {
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
        drawLine(Color(0xFF333949), Offset(0f, size.height * .5f), Offset(size.width, size.height * .5f), 1f)
        drawPath(path, color = line, style = Stroke(width = 3f, cap = StrokeCap.Round))
    }
}

@Composable
private fun MetricCard(title: String, value: String, detail: String, provenance: String, trend: List<Float> = emptyList()) {
    Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
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
    Card(shape = RoundedCornerShape(16.dp), colors = CardDefaults.cardColors(containerColor = Color(0xFF262D3B))) {
        Row(Modifier.padding(14.dp), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.Top) {
            Box(Modifier.size(34.dp).clip(RoundedCornerShape(10.dp)).background(Color(0xFF3B4361)), contentAlignment = Alignment.Center) {
                Icon(Icons.Outlined.Info, null, tint = Color(0xFFB7C1FF))
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
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(13.dp)) {
        item { PageTitle("Good to see you, $alias.", "Patient-scoped physiological workspace • $patientId") }
        item {
            Card(shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(containerColor = Color(0xFF28314D))) {
                Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                    Avatar("M", alias)
                    Spacer(Modifier.width(14.dp))
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text("Personal baseline", style = MaterialTheme.typography.titleMedium, color = Color.White)
                        Text("Illustrative completeness • not clinical certainty", style = MaterialTheme.typography.bodySmall, color = Color(0xFFC4CDE5))
                        LinearProgressIndicator(progress = 0.72f, Modifier.fillMaxWidth(), color = Color(0xFF63D8C3), trackColor = Color(0xFF3D4661))
                    }
                    Spacer(Modifier.width(12.dp))
                    Text("72%", style = MaterialTheme.typography.headlineSmall, color = Color.White, fontWeight = FontWeight.ExtraBold)
                }
            }
        }
        item { Text("Today's signals", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold) }
        item { MetricCard("Heart rate", "88 bpm", "Illustrative resting-window example", "DEMO_DATA", listOf(82f,85f,87f,84f,91f,88f,89f)) }
        item { MetricCard("HRV • RMSSD", "31 ms", "Pulse-derived feature; not interchangeable with ECG HRV", "DEMO_DATA", listOf(35f,32f,30f,36f,28f,31f,31f)) }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Box(Modifier.weight(1f)) { MetricCard("Skin temperature", "32.7 °C", "Validity-gated skin temperature", "DEMO_DATA", listOf(32.5f,32.7f,32.6f,32.8f,32.7f)) }
                Box(Modifier.weight(1f)) { MetricCard("Activity", "24%", "Illustrative motion index", "DEMO_DATA", listOf(29f,22f,27f,24f,26f,21f)) }
            }
        }
        item {
            Card(shape = RoundedCornerShape(16.dp), colors = CardDefaults.cardColors(containerColor = Color(0xFF222935))) {
                Column(Modifier.padding(15.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Outlined.Psychology, null, tint = Color(0xFFA9B7FF))
                        Spacer(Modifier.width(8.dp))
                        Text("CHRONO-PCOS", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        Spacer(Modifier.weight(1f))
                        ProvenanceBadge("RESEARCH MODULE")
                    }
                    Text("Disease-specific module inside ENDO-TWIN. A wearable stream alone is not a PCOS diagnostic criterion; disease-model context must use appropriate clinical evidence.")
                    Row(horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                        ProvenanceBadge("CLINICAL GATE", "warn")
                        ProvenanceBadge("VALIDATION: NOT ESTABLISHED", "error")
                    }
                }
            }
        }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                OutlinedButton(onClick = {}, Modifier.weight(1f)) { Text("Symptoms") }
                OutlinedButton(onClick = {}, Modifier.weight(1f)) { Text("Cycle") }
                OutlinedButton(onClick = {}, Modifier.weight(1f)) { Text("Reports") }
            }
        }
        item { Text("Research / risk-screening output — not a medical diagnosis.", color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold) }
    }
}

@Composable
private fun HealthScreen(patientId: String) {
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(13.dp)) {
        item { PageTitle("My Health", "Longitudinal context, personal baseline and data quality • $patientId") }
        item {
            Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilterChip(selected = true, onClick = {}, label = { Text("30 days") })
                FilterChip(selected = false, onClick = {}, label = { Text("90 days") })
                FilterChip(selected = false, onClick = {}, label = { Text("All time") })
            }
        }
        item { MetricCard("Personal baseline", "72% complete", "Illustrative coverage only", "DEMO_DATA", listOf(56f,61f,64f,68f,72f)) }
        item { MetricCard("Recovery context", "UNKNOWN", "No validated recovery model is active", "UNKNOWN") }
        item {
            Card(shape = RoundedCornerShape(16.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                Column(Modifier.padding(15.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                    Text("How ENDO-TWIN interprets change", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    listOf("Personal baseline", "Repeated measurements + quality", "Persistence / change over time", "Patient-reported or clinical context").forEachIndexed { index, item ->
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                            Box(Modifier.size(24.dp).clip(CircleShape).background(Color(0xFF2A4A48)), contentAlignment = Alignment.Center) {
                                Text("\${index + 1}", color = Color(0xFF7DE1C7), fontWeight = FontWeight.Bold)
                            }
                            Text(item)
                        }
                    }
                }
            }
        }
        item {
            SectionTitle("Provenance legend", "Source classification stays visible.")
            Spacer(Modifier.height(7.dp))
            Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                listOf("MEASURED","DERIVED","CLINICALLY_ENTERED","PATIENT-REPORTED","IMAGE-DERIVED","MODEL-INFERRED","DEMO_DATA","UNKNOWN").forEach { ProvenanceBadge(it) }
            }
        }
    }
}

@Composable
private fun SectionTitle(title: String, subtitle: String? = null) {
    Column(verticalArrangement = Arrangement.spacedBy(3.dp)) {
        Text(title, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
        subtitle?.let { Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) }
    }
}

@Composable
private fun MeasureScreen(patientId: String) {
    var selected by remember { mutableStateOf("Signals") }
    val filters = listOf("Signals", "Quality", "Pipeline", "Models")
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(13.dp)) {
        item { PageTitle("Measurements", "Acquisition → quality → features → provenance • $patientId") }
        item {
            Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                filters.forEach { f -> FilterChip(selected = selected == f, onClick = { selected = f }, label = { Text(f) }) }
            }
        }
        when (selected) {
            "Signals" -> {
                item { MetricCard("PPG", "20 Hz transport", "MAX30102 packet stream • raw signal path", "DEMO_DATA", listOf(2f,5f,3f,6f,4f,8f,5f)) }
                item { MetricCard("GSR / EDA", "Tonic + phasic", "Conductance proxy • processed at slower channel rate", "DEMO_DATA") }
                item { MetricCard("Motion", "6-axis IMU", "Acceleration + gyro → activity context", "DEMO_DATA") }
                item { MetricCard("Temperature", "32.7 °C", "Range / validity-gated sensor channel", "DEMO_DATA", listOf(32.5f,32.6f,32.7f,32.8f,32.7f)) }
            }
            "Quality" -> item {
                Card(shape = RoundedCornerShape(16.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                    Column(Modifier.padding(15.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                        Text("Channel-aware quality gates", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        listOf("PPG" to 0.94f, "IMU" to 0.98f, "GSR" to 0.91f, "Temperature" to 0.97f).forEach { (name, value) ->
                            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                Row { Text(name); Spacer(Modifier.weight(1f)); Text(String.format("%.0f%%", value * 100), fontWeight = FontWeight.Bold) }
                                LinearProgressIndicator(progress = value, Modifier.fillMaxWidth(), color = Color(0xFF63D8C3), trackColor = Color(0xFF393F4D))
                            }
                        }
                        Text("Engineering gates reject missing, stale, flatline or low-quality channels; they do not create clinical validity.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
            "Pipeline" -> item {
                Card(shape = RoundedCornerShape(16.dp)) {
                    Column(Modifier.padding(15.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("Processing pipeline", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        Text("CRC → decode → filtering → artifact rejection → feature extraction → quality → provenance → disease-model gate")
                        ProvenanceBadge("MEASURED → DERIVED → MODEL-INFERRED", "derived")
                    }
                }
            }
            "Models" -> item {
                Card(shape = RoundedCornerShape(16.dp)) {
                    Column(Modifier.padding(15.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("Model separation", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        Text("Observed data and disease-model outputs stay on separate layers. CHRONO-PCOS requires disease-specific evidence and remains clinically unvalidated.")
                        ProvenanceBadge("UNKNOWN / NOT RUN when evidence gate fails", "warn")
                    }
                }
            }
        }
        item { Text("Engineering validation is not clinical validation.", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.error) }
    }
}

@Composable
private fun TimelineScreen(patientId: String) {
    val events = listOf(
        "Sensor session" to "DEMO_DATA • illustrative session • 20 Sep 2026",
        "Symptom entry" to "PATIENT-REPORTED • example context",
        "Cycle event" to "CLINICALLY_ENTERED • example context",
        "Baseline update" to "DERIVED • repeated observations",
        "Ultrasound study" to "IMAGE-DERIVED • unsupported anatomy remains UNKNOWN",
        "Model gate" to "MODEL-INFERRED only after disease-specific evidence gate"
    )
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(11.dp)) {
        item { PageTitle("Timeline", "Chronological and patient-scoped • $patientId") }
        item {
            Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                AssistChip(onClick = {}, label = { Text("All") }, leadingIcon = { Icon(Icons.Default.FilterList, null) })
                AssistChip(onClick = {}, label = { Text("Signals") })
                AssistChip(onClick = {}, label = { Text("Clinical") })
                AssistChip(onClick = {}, label = { Text("Models") })
            }
        }
        items(events) { (title, detail) ->
            Card(shape = RoundedCornerShape(15.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                Row(Modifier.padding(14.dp), verticalAlignment = Alignment.Top) {
                    Box(Modifier.size(11.dp).clip(CircleShape).background(Color(0xFF63D8C3)))
                    Spacer(Modifier.width(13.dp))
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text(title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        Text(detail, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
        }
    }
}

@Composable
private fun ConnectionScreen() {
    val scope = rememberCoroutineScope()
    var endpoint by remember { mutableStateOf("") }
    var code by remember { mutableStateOf("") }
    var status by remember { mutableStateOf("Not connected") }
    var detail by remember { mutableStateOf("Use Doctor → Mobile Link to get the workstation address and 6-digit code.") }
    var token by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }

    fun request(action: suspend () -> String) {
        if (busy) return
        busy = true
        scope.launch {
            try {
                val json = JSONObject(action())
                if (json.optBoolean("paired", false)) {
                    token = json.optString("token").takeIf { it.isNotBlank() }
                    status = "Connected"
                    detail = "Paired to ${json.optString("server_name", "ENDO-TWIN Workstation")}."
                } else {
                    status = json.optString("status", "Completed")
                    detail = json.optString("message", "Request completed.")
                }
            } catch (e: Exception) {
                status = "Connection failed"
                detail = e.message ?: "Check address, code, Wi-Fi and firewall."
            } finally {
                busy = false
            }
        }
    }

    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(13.dp)) {
        item { PageTitle("Connect", "Pair with the Doctor Workstation on a trusted local network.") }
        item {
            Card(shape = RoundedCornerShape(16.dp), colors = CardDefaults.cardColors(containerColor = Color(0xFF25304A))) {
                Row(Modifier.padding(15.dp), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.Top) {
                    Icon(Icons.Outlined.Link, null, tint = Color(0xFFB3BCFF))
                    Column {
                        Text(status, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        Text(detail, style = MaterialTheme.typography.bodySmall, color = Color(0xFFC5CDE1))
                    }
                }
            }
        }
        item { OutlinedTextField(endpoint, { endpoint = it }, label = { Text("Doctor workstation address") }, placeholder = { Text("192.168.1.20:7777") }, singleLine = true, modifier = Modifier.fillMaxWidth()) }
        item { OutlinedTextField(code, { code = it.filter(Char::isDigit).take(6) }, label = { Text("6-digit pairing code") }, singleLine = true, modifier = Modifier.fillMaxWidth()) }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                OutlinedButton(onClick = { request { getJson(endpointFor(endpoint, "/v1/health")) } }, Modifier.weight(1f), enabled = !busy && endpoint.isNotBlank()) { Text("Test") }
                Button(onClick = { request { postJson(endpointFor(endpoint, "/v1/pair"), JSONObject().put("code", code).toString()) } }, Modifier.weight(1f), enabled = !busy && endpoint.isNotBlank() && code.length == 6) { Text("Pair") }
            }
        }
        item {
            Card(shape = RoundedCornerShape(16.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                Column(Modifier.padding(15.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Session transfer", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Text("This build intentionally sends DEMO_DATA. A future real-device package must be populated from patient-scoped local records and preserve provenance.")
                    Button(
                        onClick = {
                            val t = token
                            if (t == null) {
                                status = "Pair first"
                                detail = "Enter workstation address + code, then press Pair."
                                return@Button
                            }
                            request {
                                val payload = JSONObject()
                                    .put("schema_version", "1.0")
                                    .put("source_app", "ENDO-TWIN Patient Android")
                                    .put("patient_id", "DEMO-001")
                                    .put("label", "DEMO_DATA")
                                    .put("provenance", "DEMO_DATA")
                                    .put("created_at_epoch_ms", System.currentTimeMillis())
                                    .put("measurements", JSONObject().put("heart_rate_bpm", 72).put("hrv_rmssd_ms", 48).put("skin_temperature_c", 32.5).put("activity_index", 35))
                                    .put("note", "Demonstration payload only; not a clinical record.")
                                postJson(endpointFor(endpoint, "/v1/upload"), payload.toString(), t)
                            }
                        },
                        Modifier.fillMaxWidth(),
                        enabled = !busy && token != null
                    ) { Text("Send session") }
                }
            }
        }
        item { Text("Security: research LAN bridge only. Production deployment requires encryption, authentication, authorization, auditability and threat modelling.", color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.labelSmall) }
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
