package org.chronopcos.doctor

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import org.chronopcos.doctor.ui.theme.EndoTwinTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            EndoTwinTheme { DoctorApp() }
        }
    }
}

private data class DemoPatient(
    val id: String,
    val alias: String,
    val status: String,
    val lastSeen: String,
    val quality: String
)

private val demoPatients = listOf(
    DemoPatient("DEMO-001", "Research demo 001", "Needs review", "19 Sep 2026", "0.91"),
    DemoPatient("DEMO-002", "Research demo 002", "Stable demo", "18 Sep 2026", "0.84"),
    DemoPatient("DEMO-003", "Research demo 003", "Incomplete data", "16 Sep 2026", "0.58")
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DoctorApp() {
    var selectedPatient by remember { mutableStateOf<DemoPatient?>(null) }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("ENDO-TWIN", fontWeight = FontWeight.Bold)
                        Text(
                            if (selectedPatient == null) "Doctor research workstation"
                            else "Patient workspace • " + selectedPatient!!.id,
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                },
                navigationIcon = {
                    if (selectedPatient != null) {
                        IconButton(onClick = { selectedPatient = null }) {
                            Icon(Icons.Default.ArrowBack, contentDescription = "Back to patients")
                        }
                    }
                },
                actions = {
                    Surface(shape = RoundedCornerShape(50), color = MaterialTheme.colorScheme.tertiaryContainer) {
                        Text("DEMO", Modifier.padding(horizontal = 12.dp, vertical = 7.dp), style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold)
                    }
                    Spacer(Modifier.width(12.dp))
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background)
            )
        }
    ) { padding ->
        if (selectedPatient == null) {
            DoctorDashboard(Modifier.padding(padding), onOpen = { selectedPatient = it })
        } else {
            PatientWorkspace(Modifier.padding(padding), selectedPatient!!)
        }
    }
}

@Composable
private fun DoctorDashboard(modifier: Modifier, onOpen: (DemoPatient) -> Unit) {
    LazyColumn(
        modifier.fillMaxSize(),
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item {
            Text("Review queue", style = MaterialTheme.typography.displaySmall)
            Text("Multi-patient workstation • every workspace is explicitly scoped.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        item {
            Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer), shape = RoundedCornerShape(22.dp)) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                    Text("Research workflow", style = MaterialTheme.typography.titleMedium)
                    Text("Patient → measurements → quality → baseline → longitudinal context → research model → provenance → report")
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Chip("3 demo patients")
                        Chip("offline-first")
                        Chip("provenance visible")
                    }
                }
            }
        }
        item {
            SectionCard("Pending review", "2 demo workspaces", "Illustrative queue only. Real workflows should be backed by authorization and patient-scoped database queries.")
        }
        item {
            SectionCard("Data quality attention", "1 incomplete demo", "Low quality should lower downstream confidence and should never be silently repaired into fabricated observations.")
        }
        item { Text("Patients", style = MaterialTheme.typography.titleLarge) }
        items(demoPatients) { patient ->
            Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(20.dp), onClick = { onOpen(patient) }) {
                Column(Modifier.padding(17.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(patient.alias, style = MaterialTheme.typography.titleMedium)
                            Text(patient.id, color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.labelLarge)
                        }
                        Chip(patient.status)
                    }
                    Text("Last activity • " + patient.lastSeen, style = MaterialTheme.typography.bodySmall)
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("Illustrative channel quality", style = MaterialTheme.typography.bodySmall)
                        Spacer(Modifier.width(10.dp))
                        LinearProgressIndicator(progress = { patient.quality.toFloat() }, Modifier.weight(1f))
                        Spacer(Modifier.width(10.dp))
                        Text(patient.quality, style = MaterialTheme.typography.labelMedium)
                    }
                    Text("DEMO_DATA • open to switch entire context to " + patient.id, color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.labelSmall)
                }
            }
        }
        item {
            Text("Research / risk-screening output — not a medical diagnosis.", color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.SemiBold)
        }
    }
}

@Composable
private fun PatientWorkspace(modifier: Modifier, patient: DemoPatient) {
    var tab by remember { mutableStateOf("Overview") }
    val tabs = listOf("Overview", "Physiology", "Signals", "Ultrasound", "Models", "Reports", "Audit")
    LazyColumn(modifier.fillMaxSize(), contentPadding = PaddingValues(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Card(shape = RoundedCornerShape(22.dp)) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
                    Text(patient.alias, style = MaterialTheme.typography.headlineSmall)
                    Text(patient.id, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Chip(patient.status)
                        Chip("DEMO_DATA")
                    }
                    Text(
                        "Patient context lock: all cards below are scoped to " + patient.id + ". No other demo patient is referenced in this workspace.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                tabs.forEach { name ->
                    FilterChip(selected = tab == name, onClick = { tab = name }, label = { Text(name) })
                }
            }
        }
        when (tab) {
            "Overview" -> {
                item { SectionCard("Observed examples", "HR 72 bpm", "DEMO_DATA • illustrative example; not a live measurement.") }
                item { SectionCard("Derived examples", "RMSSD 48 ms", "DEMO_DATA • derived feature example; signal quality and acquisition context matter.") }
                item { SectionCard("Baseline", "Illustrative 10-observation window", "A personal baseline requires enough valid observations and should remain patient-scoped.") }
                item { SafetyCard("No clinical diagnosis", "Research output is separated from observed/entered data and carries uncertainty + limitations.") }
            }
            "Physiology" -> {
                item { SectionCard("Heart rate", "72 bpm", "DEMO_DATA • illustrative value • active sensor provenance is required for real data.") }
                item { SectionCard("HRV", "48 ms RMSSD", "DEMO_DATA • illustrative pulse-derived feature.") }
                item { SectionCard("Activity", "35%", "DEMO_DATA • illustrative motion index.") }
                item { SectionCard("Temperature", "32.5 °C", "DEMO_DATA • illustrative skin-temperature example.") }
            }
            "Signals" -> {
                item { SectionCard("PPG", "20 Hz", "Raw/filtered PPG example • quality should be per channel.") }
                item { SectionCard("GSR", "Tonic + phasic", "Electrodermal example • artifact handling remains explicit.") }
                item { SectionCard("Motion", "6-axis IMU", "MPU6050 example • activity and motion artifact context.") }
                item { SafetyCard("Missing is a state", "Long gaps should remain missing; bounded interpolation should carry a quality penalty.") }
            }
            "Ultrasound" -> {
                item { SectionCard("Study provenance", "IMAGE-DERIVED", "The image can be stored and quality-checked; unsupported anatomical features remain UNKNOWN.") }
                item { SectionCard("Feature state", "UNKNOWN when unsupported", "Do not invent cyst count, volume, morphology, accuracy, or confidence without validated labelled evidence.") }
                item { SafetyCard("Model gate", "Image inference requires an actual trained and validated model", "A missing model must produce an insufficient/unknown state, not a fabricated probability.") }
            }
            "Models" -> {
                item { SectionCard("CHRONO-PCOS", "Research module", "Disease-specific model inside ENDO-TWIN • clinical validation NOT ESTABLISHED.") }
                item { SectionCard("Model confidence", "Context-dependent", "Confidence is model/data quality context, not clinical certainty.") }
                item { SectionCard("Inputs", "Measured + derived + entered", "Only supported provenance contributes to the appropriate model layer.") }
                item { SafetyCard("Explainability", "Show model name, version, dataset, validation strategy, limitations, and uncertainty.") }
            }
            "Reports" -> {
                item { SectionCard("Report", "Patient-scoped", "Report generation preserves provenance, uncertainty, model version, and limitations.") }
                item { SectionCard("Sharing", "Deliberate export", "No automatic exposure of another patient’s report; sharing remains controlled.") }
            }
            "Audit" -> {
                item { SectionCard("Audit trail", "Timestamped", "Track patient-scoped review/export/model/report actions.") }
                item { SectionCard("Privacy", "Local-first", "The mobile research workstation is designed around local data boundaries; real deployments need authorization controls.") }
                item { SafetyCard("Demo boundary", "DEMO_DATA is not a clinical record", "Illustrative patients, values, provider entries, and distances are intentionally separated from real-world data.") }
            }
        }
        item {
            Text("Research / risk-screening output — not a medical diagnosis.", color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.SemiBold)
        }
    }
}

@Composable
private fun SectionCard(title: String, value: String, detail: String) {
    Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(20.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
            Text(title, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(value, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
            Text(detail, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun SafetyCard(title: String, detail: String, detail2: String? = null) {
    Card(shape = RoundedCornerShape(20.dp), colors = CardDefaults.cardColors(containerColor = Color(0xFF15263A))) {
        Row(Modifier.padding(16.dp), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.Top) {
            Icon(Icons.Default.Shield, null, tint = MaterialTheme.colorScheme.secondary)
            Column(verticalArrangement = Arrangement.spacedBy(5.dp)) {
                Text(title, style = MaterialTheme.typography.titleMedium)
                Text(detail)
                detail2?.let { Text(it, color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodySmall) }
            }
        }
    }
}

@Composable
private fun Chip(text: String) {
    Surface(shape = RoundedCornerShape(50), color = MaterialTheme.colorScheme.primaryContainer) {
        Text(text, Modifier.padding(horizontal = 9.dp, vertical = 5.dp), style = MaterialTheme.typography.labelSmall)
    }
}
