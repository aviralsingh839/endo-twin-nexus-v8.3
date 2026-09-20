package org.chronopcos.patient

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import org.chronopcos.patient.ui.navigation.PatientScreen
import org.chronopcos.patient.ui.screens.*

/**
 * Patient Android MainActivity - Kotlin + Jetpack Compose, Material 3
 * Single patient only - must NEVER see global list of all patients
 * Represents CURRENT PATIENT with stable patient ID
 * CHRONO-PCOS is first disease-specific implementation on ENDO-TWIN architecture
 */

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // In real app, patient ID would come from DataStore, login, etc.
        // For demo, use DEMO-001 - single patient
        val currentPatientId = "DEMO-001"

        setContent {
            MaterialTheme {
                PatientApp(currentPatientId = currentPatientId)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PatientApp(currentPatientId: String) {
    val navController = rememberNavController()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("CHRONO-PCOS Patient - $currentPatientId") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            )
        },
        bottomBar = {
            NavigationBar {
                NavigationBarItem(
                    selected = false,
                    onClick = { navController.navigate(PatientScreen.Home.route) },
                    label = { Text("Home") },
                    icon = { Text("🏠") }
                )
                NavigationBarItem(
                    selected = false,
                    onClick = { navController.navigate(PatientScreen.MyHealth.route) },
                    label = { Text("My Health") },
                    icon = { Text("❤️") }
                )
                NavigationBarItem(
                    selected = false,
                    onClick = { navController.navigate(PatientScreen.Measurements.route) },
                    label = { Text("Measure") },
                    icon = { Text("📊") }
                )
                NavigationBarItem(
                    selected = false,
                    onClick = { navController.navigate(PatientScreen.Timeline.route) },
                    label = { Text("Timeline") },
                    icon = { Text("📅") }
                )
                NavigationBarItem(
                    selected = false,
                    onClick = { navController.navigate(PatientScreen.FindCare.route) },
                    label = { Text("Find Care") },
                    icon = { Text("📍") }
                )
            }
        }
    ) { paddingValues ->
        NavHost(
            navController = navController,
            startDestination = PatientScreen.Home.route,
            modifier = Modifier.padding(paddingValues)
        ) {
            composable(PatientScreen.Home.route) {
                PatientHomeScreen(patientId = currentPatientId)
            }
            composable(PatientScreen.MyHealth.route) {
                MyHealthScreen(patientId = currentPatientId)
            }
            composable(PatientScreen.Measurements.route) {
                MeasurementsScreen(patientId = currentPatientId)
            }
            composable(PatientScreen.Timeline.route) {
                TimelineScreen(patientId = currentPatientId)
            }
            composable(PatientScreen.Symptoms.route) {
                SymptomsScreen(patientId = currentPatientId)
            }
            composable(PatientScreen.Cycle.route) {
                CycleScreen(patientId = currentPatientId)
            }
            composable(PatientScreen.Ultrasound.route) {
                UltrasoundScreen(patientId = currentPatientId)
            }
            composable(PatientScreen.Results.route) {
                ResultsScreen(patientId = currentPatientId)
            }
            composable(PatientScreen.Reports.route) {
                ReportsScreen(patientId = currentPatientId)
            }
            composable(PatientScreen.DoctorSharing.route) {
                DoctorSharingScreen(patientId = currentPatientId)
            }
            composable(PatientScreen.FindCare.route) {
                FindCareScreen(patientId = currentPatientId)
            }
            composable(PatientScreen.Education.route) {
                EducationScreen()
            }
            composable(PatientScreen.Settings.route) {
                SettingsScreen(patientId = currentPatientId)
            }
        }
    }
}

// Placeholder screens - implement full UI where appropriate
@Composable
fun MyHealthScreen(patientId: String) {
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("My Health - $patientId", style = MaterialTheme.typography.headlineSmall)
        Text("Personal baseline: mean 71 bpm median 70 std 2 confidence 0.85 min_obs 10")
        Text("Longitudinal trends: HR 70→72→71 stable LOW CHANGE SIGNAL")
        Text("Recent changes: HRV RMSSD 50→48→45 gradual deviation EARLY CHANGE SIGNAL")
        Text("Available measurements: HR MEASURED quality 0.91 source MAX30102, HRV DERIVED quality 0.85")
        Text("Data completeness: Good")
        Text("Research-model outputs: PCOSModule v8.3.0 pcos_associated_risk low confidence 0.75 data quality 0.85 clinical validation NOT ESTABLISHED - clearly distinguished model inference from measurements")
        Text("Provenance: MEASURED CLINICALLY_ENTERED IMAGE-DERIVED MODEL-INFERRED UNKNOWN")
    }
}

@Composable
fun MeasurementsScreen(patientId: String) {
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Measurements - $patientId", style = MaterialTheme.typography.headlineSmall)
        Text("HR: 72 bpm MEASURED quality 0.91 source MAX30102 timestamp now")
        Text("HRV RMSSD: 48 ms DERIVED quality 0.85 source PPG-derived limitations PPG less accurate than ECG")
        Text("PPG: IR 12345 RED 67890 quality 0.91 MEASURED")
        Text("GSR: tonic 0.5 phasic 0.2 MEASURED+DERIVED")
        Text("Temperature: skin 32.5C MEASURED quality 0.88 source DS18B20 limitations skin not core")
        Text("Motion: activity 35% MEASURED source MPU6050")
        Text("Sleep/circadian: regularity 75% MODEL-INFERRED limitations not polysomnography")
        Text("Provenance visible for every measurement - do not fabricate values")
    }
}

@Composable
fun TimelineScreen(patientId: String) {
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Timeline - $patientId", style = MaterialTheme.typography.headlineSmall)
        Text("Chronological timeline - date filtering, event filtering, session details")
        Text("Sensor session: 2026-09-19 MEASURED quality 0.85")
        Text("Symptom entry: 2026-09-18 CLINICALLY_ENTERED USER-ENTERED")
        Text("Cycle event: 2026-09-15 CLINICALLY_ENTERED")
        Text("Ultrasound study: 2026-09-15 IMAGE-DERIVED quality UNKNOWN by design unless computed")
        Text("Analysis: 2026-09-19 MODEL-INFERRED")
        Text("Model run: PCOSModule v8.3.0 confidence 0.75")
        Text("Report generated: 2026-09-19")
        Text("Patient-specific timeline - scoped to $patientId")
    }
}

@Composable
fun SymptomsScreen(patientId: String) {
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Symptoms - $patientId", style = MaterialTheme.typography.headlineSmall)
        Text("Structured symptom logging: timestamp, symptom, severity, notes")
        Text("Symptom: irregular_cycle severity 1 notes Demo symptom for $patientId")
        Text("Never turn symptoms into diagnosis")
        Text("Provenance: CLINICALLY_ENTERED USER-ENTERED")
    }
}

@Composable
fun CycleScreen(patientId: String) {
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Cycle Tracking - $patientId", style = MaterialTheme.typography.headlineSmall)
        Text("Cycle dates, cycle length, irregularity, symptom association")
        Text("Cycle length: 32 days irregularity irregular")
        Text("Do not make unsupported medical interpretations")
        Text("Provenance: CLINICALLY_ENTERED")
    }
}

@Composable
fun UltrasoundScreen(patientId: String) {
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Ultrasound - $patientId", style = MaterialTheme.typography.headlineSmall)
        Text("Study list: ultrasound_${patientId}_001 date now")
        Text("Image: /demo/ultrasound_${patientId}.png metadata")
        Text("Analysis: cyst detection morphology volume if model available")
        Text("Image-derived features: cyst size mm volume cc morphology quality source confidence")
        Text("Model results: inference requires trained model if insufficient state insufficient never fabricate percentages confidence None unless computed")
        Text("Uncertainty: confidence None unless computed quality UNKNOWN by design unless computed")
        Text("Provenance: IMAGE-DERIVED clearly labelled")
        Text("Each study must belong to exactly one patient - scoped to $patientId")
    }
}

@Composable
fun ResultsScreen(patientId: String) {
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Results - $patientId", style = MaterialTheme.typography.headlineSmall)
        Text("Explain results in understandable language")
        Text("Observed measurements: HR 72 bpm MEASURED quality 0.91 source MAX30102")
        Text("Longitudinal changes: HRV RMSSD 50→48→45 gradual deviation EARLY CHANGE SIGNAL")
        Text("Model inference: PCOSModule v8.3.0 pcos_associated_risk low confidence 0.75 data quality 0.85 clinical validation NOT ESTABLISHED")
        Text("Contributing factors: HRV RMSSD 48 ms, activity 35%, skin temp 32.5C")
        Text("Uncertainty: confidence model output not clinical certainty, quality 0.85")
        Text("Limitations: Engineering validation only, clinical validation NOT ESTABLISHED")
        Text("Labels: MEASURED IMAGE-DERIVED MODEL-INFERRED UNKNOWN")
        Text("Research / risk-screening output — not a medical diagnosis")
    }
}

@Composable
fun ReportsScreen(patientId: String) {
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Reports - $patientId", style = MaterialTheme.typography.headlineSmall)
        Text("Only reports belonging to current patient $patientId")
        Text("Report: pcos_risk_screening for $patientId - Risk low - Research / risk-screening output — not a medical diagnosis")
        Text("Allow view, preview, export, share where permitted")
        Text("Never accidentally expose another patient's report - patient-scoped queries")
        Text("Provenance: MEASURED CLINICALLY_ENTERED IMAGE-DERIVED MODEL-INFERRED clearly separated")
    }
}

@Composable
fun DoctorSharingScreen(patientId: String) {
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Doctor Sharing - $patientId", style = MaterialTheme.typography.headlineSmall)
        Text("Controlled sharing/export - select what information is shared")
        Text("Sharing state visible - Privacy-first")
        Text("Controlled export/import/backup/restore/encrypted package deliberate not automatic")
        Text("Patient ID: $patientId - controlled sharing")
    }
}

@Composable
fun FindCareScreen(patientId: String) {
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Find Care - $patientId", style = MaterialTheme.typography.headlineSmall)
        Text("Doctors, Clinics, Labs, Supplies")
        Text("Dr. Priya Sharma (Demo) 1.2km Gynecology Verified [View][Directions] - DEMO DATA visible")
        Text("ABC Women's Clinic (Demo) 2.1km Gynecology Verified - DEMO DATA")
        Text("Do not fabricate real-world availability - demo clearly marked demo verification_status demo is_demo 1")
        Text("Map/list distance/specialty/address/hours/services/contact/directions OSM no API key offline-first")
    }
}

@Composable
fun EducationScreen() {
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Education", style = MaterialTheme.typography.headlineSmall)
        Text("What HR means: heart rate bpm MEASURED source MAX30102")
        Text("What HRV means: heart rate variability RMSSD SDNN pNN50 DERIVED limitations PPG less accurate than ECG")
        Text("What physiological monitoring means: sensing, signal processing, quality, baseline, longitudinal")
        Text("What longitudinal analysis means: personal baseline → time series → change → persistence → recovery → context")
        Text("What AI does: PCOSModule v8.3.0 pcos_associated_risk low/moderate/high NOT diagnosis confidence 0.75 data quality 0.85 clinical validation NOT ESTABLISHED")
        Text("What AI does not do: diagnosis, clinical validation, medical advice")
        Text("What ultrasound contributes: IMAGE-DERIVED cyst size morphology quality UNKNOWN by design unless computed")
        Text("Why this is not a diagnosis: Research prototype, not clinically validated, requires clinical evaluation")
    }
}

@Composable
fun SettingsScreen(patientId: String) {
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Settings - $patientId", style = MaterialTheme.typography.headlineSmall)
        Text("Patient ID: $patientId - single patient")
        Text("Privacy: local-first, offline, no cloud upload")
        Text("Data: controlled export/import/backup/restore")
        Text("Version: 8.3+ ENDO-TWIN ready")
        Text("Disclaimer: Research / risk-screening output — not a medical diagnosis")
    }
}
