@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)

package org.chronopcos.doctor

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
import org.chronopcos.doctor.ui.theme.EndoTwinTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { EndoTwinTheme { DoctorApp() } }
    }
}

private data class DemoPatient(
    val id: String,
    val alias: String,
    val condition: String,
    val tier: String,
    val risk: Int,
    val quality: Float,
    val lastSeen: String
)

private val demoPatients = listOf(
    DemoPatient("Patient 021", "Mira", "CHRONO-PCOS", "High", 78, .94f, "Today 23:07"),
    DemoPatient("Patient 014", "Anika", "CHRONO-PCOS", "Elevated", 64, .91f, "Today 22:51"),
    DemoPatient("Patient 033", "Ira", "Cardiometabolic pattern", "Elevated", 58, .89f, "Today 22:13"),
    DemoPatient("Patient 009", "Rhea", "Autonomic pattern", "Moderate", 47, .93f, "Today 21:44"),
    DemoPatient("Patient 027", "Tara", "Sleep pattern", "Moderate", 42, .86f, "Today 20:38"),
    DemoPatient("Patient 041", "Noor", "CHRONO-PCOS", "Low", 23, .97f, "Today 19:52")
)

private enum class DoctorTab(val label: String) {
    Dashboard("Dashboard"),
    Patients("Patients"),
    Live("Live Monitoring"),
    Analysis("Analysis"),
    Reports("Reports"),
    Devices("Devices"),
    Mobile("Mobile"),
    Settings("Settings")
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun DoctorApp() {
    var tab by remember { mutableStateOf(DoctorTab.Dashboard) }
    var selected by remember { mutableStateOf<DemoPatient?>(null) }

    BoxWithConstraints(Modifier.fillMaxSize()) {
        val wide = maxWidth >= 700.dp
        Scaffold(
            containerColor = MaterialTheme.colorScheme.background,
            topBar = {
                TopAppBar(
                    title = {
                        Column {
                            Text("ENDO-TWIN NEXUS", fontWeight = FontWeight.ExtraBold)
                            Text(
                                if (selected == null) "Doctor research workstation" else "Patient workspace • ${selected!!.id}",
                                style = MaterialTheme.typography.labelSmall,
                                color = Color(0xFFB9C7D2)
                            )
                        }
                    },
                    navigationIcon = {
                        if (selected != null) {
                            IconButton(onClick = { selected = null; tab = DoctorTab.Patients }) {
                                Icon(Icons.Default.ArrowBack, "Back")
                            }
                        }
                    },
                    actions = {
                        Surface(shape = RoundedCornerShape(10.dp), color = MaterialTheme.colorScheme.surfaceVariant) {
                            Text("DEMO_DATA", Modifier.padding(horizontal = 10.dp, vertical = 7.dp), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurface, fontWeight = FontWeight.Bold)
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFF142B3A), titleContentColor = Color.White)
                )
            }
        ) { padding ->
            Row(Modifier.fillMaxSize().padding(padding)) {
                if (wide) {
                    NavigationRail(containerColor = MaterialTheme.colorScheme.surface) {
                        Spacer(Modifier.height(10.dp))
                        NavIcon(Icons.Outlined.Dashboard, "Dashboard", tab == DoctorTab.Dashboard) { selected = null; tab = DoctorTab.Dashboard }
                        NavIcon(Icons.Outlined.People, "Patients", tab == DoctorTab.Patients) { tab = DoctorTab.Patients }
                        NavIcon(Icons.Outlined.MonitorHeart, "Live Monitoring", tab == DoctorTab.Live) { tab = DoctorTab.Live }
                        NavIcon(Icons.Outlined.AutoGraph, "Analysis", tab == DoctorTab.Analysis) { tab = DoctorTab.Analysis }
                        NavIcon(Icons.Outlined.Description, "Reports", tab == DoctorTab.Reports) { tab = DoctorTab.Reports }
                        NavIcon(Icons.Outlined.Sensors, "Devices", tab == DoctorTab.Devices) { tab = DoctorTab.Devices }
                        
                        NavIcon(Icons.Outlined.Link, "Mobile", tab == DoctorTab.Mobile) { tab = DoctorTab.Mobile }
                        NavIcon(Icons.Outlined.Settings, "Settings", tab == DoctorTab.Settings) { tab = DoctorTab.Settings }
                    }
                }
                if (selected != null) {
                    PatientWorkspace(selected!!)
                } else when (tab) {
                    DoctorTab.Dashboard -> Dashboard(onOpen = { selected = it })
                    DoctorTab.Patients -> Patients(onOpen = { selected = it })
                    DoctorTab.Models -> ModelPage()
                    DoctorTab.Hardware -> HardwarePage()
                    DoctorTab.Mobile -> MobilePage()
                    DoctorTab.Settings -> SettingsPage()
                }
            }
        }
    }
}

@Composable
private fun NavIcon(icon: androidx.compose.ui.graphics.vector.ImageVector, label: String, selected: Boolean, onClick: () -> Unit) {
    NavigationRailItem(selected = selected, onClick = onClick, icon = { Icon(icon, label) }, label = { Text(label, fontSize = 9.sp) })
}

@Composable
private fun Dashboard(onOpen: (DemoPatient) -> Unit) {
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(13.dp)) {
        item { PageTitle("Doctor Dashboard", "Cross-patient review surface • research workspace") }
        item {
            Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                InfoChip("23 active"); InfoChip("2 needs review"); InfoChip("5 flagged"); InfoChip("V8.6.1")
            }
        }
        item {
            Card(shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(containerColor = Color(0xFF28314D))) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Review queue", style = MaterialTheme.typography.titleMedium, color = Color.White, fontWeight = FontWeight.Bold)
                    Text("Priority → research context → condition. Demo tiers are synthetic UI examples only.", color = Color(0xFFC6CEE2), style = MaterialTheme.typography.bodySmall)
                    Row(horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                        StatusChip("High", "error"); StatusChip("Elevated", "warn"); StatusChip("Unknown")
                    }
                }
            }
        }
        item { SectionTitle("Recently synced", "Select a patient to open the full patient-scoped workspace.") }
        items(demoPatients.take(5)) { p -> PatientRow(p, onOpen) }
        item { SectionCard("Live sensor monitoring", "CRC-checked • quality-gated", "PPG, HRV, IMU, GSR and temperature. Live measurements remain separate from disease-model output.") }
        item { Text("Research / risk-screening output — not a medical diagnosis.", color = MaterialTheme.colorScheme.error, fontWeight = FontWeight.Bold) }
    }
}

@Composable
private fun Patients(onOpen: (DemoPatient) -> Unit) {
    var query by remember { mutableStateOf("") }
    var filter by remember { mutableStateOf("All") }
    val conditions = listOf("All", "CHRONO-PCOS", "Cardiometabolic pattern", "Autonomic pattern", "Sleep pattern")
    val rows = demoPatients.filter { p ->
        (filter == "All" || p.condition == filter) &&
            (query.isBlank() || "${p.alias} ${p.id} ${p.condition}".contains(query, ignoreCase = true))
    }
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { PageTitle("Patients", "Registry • condition/module filter • patient-scoped context") }
        item { OutlinedTextField(query, { query = it }, singleLine = true, label = { Text("Search patients") }, modifier = Modifier.fillMaxWidth()) }
        item {
            Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                conditions.forEach { c -> FilterChip(selected = filter == c, onClick = { filter = c }, label = { Text(c) }) }
            }
        }
        items(rows) { p -> PatientRow(p, onOpen) }
        item { Text("Demo tiers and research-context values are synthetic showcase fields, not clinical severity or validated probabilities.", color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.labelSmall) }
    }
}

@Composable
private fun PatientRow(patient: DemoPatient, onOpen: (DemoPatient) -> Unit) {
    Card(onClick = { onOpen(patient) }, shape = RoundedCornerShape(12.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface), border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outline)) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.size(42.dp).clip(CircleShape).background(MaterialTheme.colorScheme.primary), contentAlignment = Alignment.Center) {
                    Icon(Icons.Outlined.Face, null, tint = Color.White)
                }
                Spacer(Modifier.width(10.dp))
                Column(Modifier.weight(1f)) {
                    Text(patient.alias, fontWeight = FontWeight.Bold)
                    Text(patient.id, color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.labelMedium)
                }
                StatusChip(patient.tier, if (patient.tier == "High") "error" else if (patient.tier == "Elevated") "warn" else "neutral")
            }
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(patient.condition, style = MaterialTheme.typography.bodyMedium)
                    Text(patient.lastSeen, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text("${patient.risk}%", fontWeight = FontWeight.ExtraBold)
                    Text(String.format("%.0f%% quality", patient.quality * 100), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            LinearProgressIndicator(progress = patient.quality, Modifier.fillMaxWidth(), color = Color(0xFF63D8C3), trackColor = Color(0xFF39404E))
        }
    }
}

@Composable
private fun PatientWorkspace(patient: DemoPatient) {
    var tab by remember { mutableStateOf("Overview") }
    val tabs = listOf("Overview", "Physiology", "Signals", "Ultrasound", "AI / Models", "Reports", "Audit")
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Card(shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                Row(Modifier.padding(15.dp), verticalAlignment = Alignment.CenterVertically) {
                    Box(Modifier.size(50.dp).clip(CircleShape).background(MaterialTheme.colorScheme.primary), contentAlignment = Alignment.Center) {
                        Icon(Icons.Outlined.Face, null, tint = Color.White, modifier = Modifier.size(30.dp))
                    }
                    Spacer(Modifier.width(12.dp))
                    Column(Modifier.weight(1f)) {
                        Text(patient.alias, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.ExtraBold)
                        Text("${patient.id} • patient-scoped", color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                        Text("${patient.condition} • ${patient.lastSeen}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    StatusChip(patient.tier, if (patient.tier == "High") "error" else if (patient.tier == "Elevated") "warn" else "neutral")
                }
            }
        }
        item {
            Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                tabs.forEach { t -> FilterChip(selected = tab == t, onClick = { tab = t }, label = { Text(t) }) }
            }
        }
        when (tab) {
            "Overview" -> {
                item { TrendCard("Heart rate", "88 bpm", listOf(82f,85f,87f,84f,91f,88f,89f), "MEASURED") }
                item { TrendCard("HRV • RMSSD", "31 ms", listOf(35f,32f,30f,36f,28f,31f,31f), "DERIVED") }
                item { TrendCard("Skin temperature", "32.7 °C", listOf(32.5f,32.7f,32.6f,32.8f,32.7f), "MEASURED") }
                item { SectionCard("Research interpretation", "Not a diagnosis", "Sensor observations, clinical inputs and disease-model context remain separate.") }
            }
            "Physiology" -> {
                item { TrendCard("Heart rate", "88 bpm", listOf(82f,85f,87f,84f,91f,88f,89f), "MEASURED") }
                item { TrendCard("HRV", "31 ms RMSSD", listOf(35f,32f,30f,36f,28f,31f,31f), "DERIVED") }
                item { TrendCard("Activity", "24%", listOf(29f,22f,27f,24f,26f,21f), "DERIVED") }
            }
            "Signals" -> {
                item { SectionCard("PPG", "20 Hz packet stream", "CRC-checked input → filtered waveform → peak detection → quality gate.") }
                item { SectionCard("GSR / EDA", "10 Hz processing", "Tonic and phasic conductance features; source quality remains explicit.") }
                item { SectionCard("IMU", "6-axis motion", "Acceleration + gyro context for activity and motion-artifact handling.") }
                item { SectionCard("Quality", "Channel-aware", "Missing, stale, flatline and implausible states remain explicit.") }
            }
            "Ultrasound" -> {
                item { SectionCard("Image evidence", "IMAGE-DERIVED", "Source image and patient provenance remain attached.") }
                item { SectionCard("Anatomical output", "UNKNOWN unless validated", "No follicle counts, ovarian morphology or accuracy claims are invented.") }
            }
            "AI / Models" -> {
                item { SectionCard("CHRONO-PCOS", "Research module", "Disease-specific module inside ENDO-TWIN • clinical validation NOT ESTABLISHED.") }
                item { SectionCard("Evidence gate", "Clinical context required", "Wearable physiology alone must not create a disease-specific result.") }
                item { SectionCard("Index interpretation", "Heuristic / uncalibrated", "A research index is not a probability, diagnosis or measure of model accuracy.") }
            }
            "Reports" -> {
                item { SectionCard("Report assembly", "Patient → acquisition → quality → features → baseline → model → uncertainty", "Traceable report structure.") }
                item { SectionCard("Export", "Deliberate", "Keep patient scope explicit and preserve provenance.") }
            }
            "Audit" -> {
                item { SectionCard("Audit", "Timestamped", "Patient review, model, report and export actions should remain traceable.") }
                item { SectionCard("Privacy", "Local-first", "This prototype is not production clinical security.") }
            }
        }
        item { Text("Research / risk-screening output — not a medical diagnosis.", color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Bold) }
    }
}

@Composable
private fun TrendCard(title: String, value: String, values: List<Float>, provenance: String) {
    Card(shape = RoundedCornerShape(16.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(title, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Spacer(Modifier.weight(1f))
                StatusChip(provenance, if (provenance == "MEASURED") "good" else "info")
            }
            Text(value, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.ExtraBold)
            MiniTrend(values)
        }
    }
}

@Composable
private fun MiniTrend(values: List<Float>) {
    Canvas(Modifier.fillMaxWidth().height(86.dp)) {
        if (values.size < 2) return@Canvas
        val min = values.minOrNull() ?: return@Canvas
        val max = values.maxOrNull() ?: return@Canvas
        val span = (max - min).coerceAtLeast(.001f)
        val path = Path()
        values.forEachIndexed { i, v ->
            val x = size.width * i / values.lastIndex.coerceAtLeast(1)
            val y = size.height - (v - min) / span * size.height
            if (i == 0) path.moveTo(x, y) else path.lineTo(x, y)
        }
        drawLine(Color(0xFF353B49), Offset(0f, size.height * .55f), Offset(size.width, size.height * .55f), 1f)
        drawPath(path, color = Color(0xFF63D8C3), style = Stroke(width = 3f, cap = StrokeCap.Round))
    }
}

@Composable
private fun ModelPage() {
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { PageTitle("AI / Models", "Transparent research model registry") }
        item { SectionCard("CHRONO-PCOS", "Research module", "First disease-specific module inside ENDO-TWIN. Clinical validation is NOT ESTABLISHED.") }
        item { SectionCard("Evidence gate", "Enabled", "Disease-specific context is required; wearable physiology is contextual rather than diagnostic.") }
        item { SectionCard("Uncertainty", "Visible", "Data quality, missing evidence, model version and limitations should remain beside results.") }
        item { SectionCard("Validation", "NOT ESTABLISHED", "Synthetic metrics are never promoted to clinical performance.") }
    }
}

@Composable
private fun HardwarePage() {
    val context = androidx.compose.ui.platform.LocalContext.current
    val client = remember { org.chronopcos.doctor.wifi.EndoTwinTcpClient(context) }
    var state by remember { mutableStateOf(client.state) }
    var host by remember { mutableStateOf("192.168.4.1") }
    var portText by remember { mutableStateOf("7777") }
    var device by remember { mutableStateOf<String?>(null) }
    var packets by remember { mutableStateOf(0) }
    var latest by remember { mutableStateOf("Waiting for CP2…") }
    var error by remember { mutableStateOf<String?>(null) }

    DisposableEffect(client) {
        client.onState = { state = it }
        client.onDevice = { device = it }
        client.onError = { error = it }
        client.onSample = { sample -> packets += 1; latest = "IR ${sample.ir} • Red ${sample.red} • GSR ${sample.gsr} • status ${sample.status}" }
        onDispose { client.disconnect() }
    }

    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { PageTitle("Hardware Lab", "ESP32-S3 wearable Wi-Fi/TCP • live engineering validation") }
        item {
            Card(shape = RoundedCornerShape(16.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(host, { host = it }, label = { Text("ESP32-S3 IP / host") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(portText, { portText = it }, label = { Text("TCP port") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    Text("TCP ${state.name} • ${device ?: "Not connected"}", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.ExtraBold)
                    Text("$packets CP2 packets • $latest")
                    error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
                }
            }
        }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = { client.connect(host, portText.toIntOrNull() ?: 7777); error = null }, Modifier.weight(1f)) { Text("Connect ESP32-S3") }
                OutlinedButton(onClick = { client.disconnect() }, Modifier.weight(1f)) { Text("Disconnect") }
            }
        }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = { client.ping() }, Modifier.weight(1f), enabled = state == org.chronopcos.doctor.wifi.EndoTwinTcpClient.State.CONNECTED) { Text("PING") }
                OutlinedButton(onClick = { client.whoAmI() }, Modifier.weight(1f), enabled = state == org.chronopcos.doctor.wifi.EndoTwinTcpClient.State.CONNECTED) { Text("WHOAMI") }
            }
        }
        item { SectionCard("Bench controller", "Arduino Mega", "USB-only CP2 bench/lab controller remains separate from the ESP32-S3 wearable.") }
        item { Text("The ESP32-S3 wearable uses Wi-Fi/TCP for the current Android link; USB serial remains available for desktop bench testing.", color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.labelSmall) }
    }
}

@Composable
private fun MobilePage() {
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { PageTitle("Mobile Link", "Patient Android pairing • trusted LAN research bridge") }
        item { SectionCard("Endpoint", "Doctor bridge • 7777", "Copy the workstation address from Desktop → Mobile Link.") }
        item { SectionCard("Pairing", "6-digit code", "Temporary token is issued only after successful pairing.") }
        item { SectionCard("Transport", "DEMO_DATA", "Current Android payload remains deliberately synthetic.") }
        item { Text("Production security requires encryption, authentication, authorization and audit logging.", color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.labelSmall) }
    }
}

@Composable
private fun SettingsPage() {
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { PageTitle("Settings", "Workstation configuration and research boundary") }
        item { SectionCard("Session mode", "Selected at startup", "DEMO MODE or LIVE SENSOR MODE is fixed for the run.") }
        item { SectionCard("Storage", "LOCAL-FIRST", "Patient-scoped research data remains local by default.") }
        item { SectionCard("Scientific status", "Research prototype", "Clinical validation and diagnostic performance are NOT ESTABLISHED.") }
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
private fun SectionTitle(title: String, subtitle: String) {
    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
        Text(title, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
        Text(subtitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun SectionCard(title: String, value: String, detail: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
            Text(title, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(value, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.ExtraBold)
            Text(detail, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun InfoChip(text: String) {
    Surface(shape = RoundedCornerShape(9.dp), color = Color(0xFF2A303D)) {
        Text(text, Modifier.padding(horizontal = 9.dp, vertical = 6.dp), style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun StatusChip(text: String, kind: String = "neutral") {
    val (bg, fg) = when (kind) {
        "good" -> Color(0xFF193F39) to Color(0xFF78D9BE)
        "info" -> Color(0xFF39345A) to Color(0xFFB8AEFF)
        "warn" -> Color(0xFF4E3C20) to Color(0xFFF0B969)
        "error" -> Color(0xFF4D2B2C) to Color(0xFFFF9C90)
        else -> Color(0xFF2A303D) to Color(0xFFBBC4D5)
    }
    Surface(shape = RoundedCornerShape(8.dp), color = bg) {
        Text(text, Modifier.padding(horizontal = 8.dp, vertical = 5.dp), style = MaterialTheme.typography.labelSmall, color = fg, fontWeight = FontWeight.Bold)
    }
}
