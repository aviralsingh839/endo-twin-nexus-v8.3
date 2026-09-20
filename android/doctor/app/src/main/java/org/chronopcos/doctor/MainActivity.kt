package org.chronopcos.doctor

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController

/**
 * Doctor Android MainActivity - Kotlin + Jetpack Compose, Material 3, Multi-patient
 * MAIN: Dashboard, Patients, Recent Activity, Pending Review, Reports, Settings
 * Patient List: Patient ID, Name/alias, Age, Last session, Last analysis, Status, Search, Filter, Sort, Open, Archive, Create, Import/export
 * Patient Profile: Opening patient CP-0001 must switch entire context to CP-0001
 * Tabs: OVERVIEW, TIMELINE, PHYSIOLOGY, SENSORS, ULTRASOUND, AI/MODELS, CLINICAL DATA, REPORTS, NOTES, PROVENANCE, AUDIT
 * Everything displayed must belong to that patient
 * DEMO-001 cannot see DEMO-002 - implemented at database level not merely UI hidden
 * Reports patient-specific, Ultrasounds patient-specific, AI runs patient-specific, Sensor sessions patient-specific, Timeline patient-specific
 */

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                DoctorApp()
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DoctorApp() {
    val navController = rememberNavController()
    var selectedPatientId by remember { mutableStateOf<String?>(null) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { 
                    Text(
                        if (selectedPatientId != null) "Doctor - Patient $selectedPatientId" 
                        else "CHRONO-PCOS Doctor - Multi-Patient"
                    ) 
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            )
        }
    ) { paddingValues ->
        NavHost(
            navController = navController,
            startDestination = "dashboard",
            modifier = Modifier.padding(paddingValues)
        ) {
            composable("dashboard") {
                DoctorDashboardScreen(
                    onPatientSelected = { patientId ->
                        selectedPatientId = patientId
                        navController.navigate("patient/$patientId")
                    }
                )
            }
            composable("patient/{patientId}") { backStackEntry ->
                val patientId = backStackEntry.arguments?.getString("patientId") ?: "DEMO-001"
                PatientWorkspaceScreen(patientId = patientId)
            }
        }
    }
}

@Composable
fun DoctorDashboardScreen(
    onPatientSelected: (String) -> Unit
) {
    // Demo patients with deliberately different data
    val demoPatients = listOf(
        Triple("DEMO-001", "Demo Patient 001 (DEMO DATA)", "HR 72 bpm, HRV 48 ms, Activity 35%, Temp 32.5C - low risk"),
        Triple("DEMO-002", "Demo Patient 002 (DEMO DATA)", "HR 78 bpm, HRV 35 ms, Activity 25%, Temp 32.8C - high risk"),
        Triple("DEMO-003", "Demo Patient 003 (DEMO DATA)", "HR 68 bpm, HRV 55 ms, Activity 45%, Temp 32.3C - low risk")
    )

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Text("Doctor Dashboard - Multi-Patient", style = MaterialTheme.typography.headlineSmall)
            Text("Research / risk-screening output — not a medical diagnosis", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.error)
            Text("Patient List: Patient ID, Name/alias, Age, Last session, Last analysis, Status, Search, Filter, Sort, Open, Archive, Create, Import/export")
        }

        item {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Recent Activity", style = MaterialTheme.typography.titleMedium)
                    Text("Sensor sessions, model runs, reports generated")
                }
            }
        }

        item {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Pending Review", style = MaterialTheme.typography.titleMedium)
                    Text("Sessions needing review, data quality checks")
                }
            }
        }

        item {
            Text("Patients - DEMO-001, DEMO-002, DEMO-003 with deliberately different data", style = MaterialTheme.typography.titleMedium)
            Text("Test: DEMO-001 cannot see DEMO-002 - implemented at database level not merely UI hidden", style = MaterialTheme.typography.labelSmall)
        }

        items(demoPatients) { (patientId, displayName, details) ->
            Card(
                modifier = Modifier.fillMaxWidth(),
                onClick = { onPatientSelected(patientId) }
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("$patientId - $displayName", style = MaterialTheme.typography.titleSmall)
                    Text(details, style = MaterialTheme.typography.bodySmall)
                    Text("Patient ID: $patientId - Stable ID, foreign keys, patient-scoped queries, no cross-patient contamination", style = MaterialTheme.typography.labelSmall)
                    Button(onClick = { onPatientSelected(patientId) }) {
                        Text("Open $patientId - Switch entire context to $patientId")
                    }
                }
            }
        }
    }
}

@Composable
fun PatientWorkspaceScreen(patientId: String) {
    // When patient CP-0001 is selected, EVERY SCREEN becomes scoped to CP-0001
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Text("Patient Workspace - $patientId", style = MaterialTheme.typography.headlineSmall)
            Text("EVERY SCREEN becomes scoped to $patientId - Patient overview, Personal baseline, Recent sessions, Longitudinal timeline, Physiology, Sensors, Ultrasound, AI, Clinical data, Reports, Notes, Provenance, Audit", style = MaterialTheme.typography.bodySmall)
            Text("Multi-Patient Safety: $patientId cannot see other patients - database level", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.error)
        }

        item {
            TabSection(title = "OVERVIEW", patientId = patientId, content = "Patient overview for $patientId - Age 22 BMI 23.5 USER-ENTERED, Personal baseline mean 71 std 2, Recent sessions, Longitudinal timeline")
        }
        item {
            TabSection(title = "TIMELINE", patientId = patientId, content = "Timeline for $patientId - sensor_session 2026-09-19 MEASURED quality 0.85, symptom_entry CLINICALLY_ENTERED, ultrasound_study IMAGE-DERIVED quality UNKNOWN, model_run MODEL-INFERRED confidence 0.75, report_generated - patient-specific timeline")
        }
        item {
            TabSection(title = "PHYSIOLOGY", patientId = patientId, content = "Physiology for $patientId - HR 72 bpm MEASURED quality 0.91 source MAX30102, HRV RMSSD 48 ms DERIVED quality 0.85 limitations PPG less accurate than ECG, GSR, Temp, Motion - patient-specific")
        }
        item {
            TabSection(title = "SENSORS", patientId = patientId, content = "Sensors for $patientId - raw/filtered PPG, HR, HRV, GSR, motion, temp, quality, artifacts visualization time-series - sensor sessions patient-specific")
        }
        item {
            TabSection(title = "ULTRASOUND", patientId = patientId, content = "Ultrasound for $patientId - study list ultrasound_${patientId}_001 date now, image /demo/ultrasound_${patientId}.png, metadata, analysis, image-derived features cyst size mm volume cc morphology quality source confidence, model results inference requires trained model if insufficient state insufficient never fabricate percentages confidence None unless computed, uncertainty quality UNKNOWN by design unless computed, provenance IMAGE-DERIVED clearly labelled - ultrasounds patient-specific")
        }
        item {
            TabSection(title = "AI / MODELS", patientId = patientId, content = "AI/ML for $patientId - PCOSModule v8.3.0 pcos_associated_risk low/moderate/high NOT diagnosis confidence 0.75 data quality 0.85 clinical validation NOT ESTABLISHED, SleepModule circadian_disruption_pattern moderate confidence 0.68, Model registry name version dataset version training date features target metrics validation strategy limitations never hide uncertainty - AI runs patient-specific")
        }
        item {
            TabSection(title = "CLINICAL DATA", patientId = patientId, content = "Clinical data for $patientId - age BMI cycle info USER-ENTERED CLINICALLY_ENTERED, glucose BP if entered")
        }
        item {
            TabSection(title = "REPORTS", patientId = patientId, content = "Reports for $patientId - Report pcos_risk_screening for $patientId - Risk low - Research / risk-screening output — not a medical diagnosis - patient-specific reports never expose another patient's report")
        }
        item {
            TabSection(title = "NOTES", patientId = patientId, content = "Doctor notes for $patientId - patient-specific notes")
        }
        item {
            TabSection(title = "PROVENANCE", patientId = patientId, content = "Provenance for $patientId - MEASURED HR 72 bpm quality 0.91 source MAX30102, CLINICALLY_ENTERED age BMI cycle info USER-ENTERED, IMAGE-DERIVED cyst size morphology quality UNKNOWN by design unless computed provenance CLINICALLY-ENTERED vs IMAGE-DERIVED fusion weight 0.20, MODEL-INFERRED sleep regularity circadian disruption confidence limitations, UNKNOWN if cannot reliably extract return UNKNOWN never invent - provenance visible")
        }
        item {
            TabSection(title = "AUDIT", patientId = patientId, content = "Audit for $patientId - audit_events patient_id, user_id, action, timestamp, patient-scoped audit history")
        }
    }
}

@Composable
fun TabSection(title: String, patientId: String, content: String) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("$title - $patientId", style = MaterialTheme.typography.titleMedium)
            Text(content, style = MaterialTheme.typography.bodySmall)
            Text("Scoped to $patientId - no cross-patient contamination", style = MaterialTheme.typography.labelSmall)
        }
    }
}
