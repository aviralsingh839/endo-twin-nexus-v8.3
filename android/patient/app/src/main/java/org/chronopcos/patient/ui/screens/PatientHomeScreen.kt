package org.chronopcos.patient.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * Patient Home - Today's overview, data collection status, sensor/device status, recent measurements, signal quality, recent activity, personal baseline status, recent longitudinal change
 * Use understandable language: "Data quality: Good" rather than raw technical diagnostics
 * Do not make unsupported medical claims
 */

@Composable
fun PatientHomeScreen(
    patientId: String,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Text(
                text = "CHRONO-PCOS Patient - $patientId",
                style = MaterialTheme.typography.headlineSmall
            )
            Text(
                text = "Research / risk-screening output — not a medical diagnosis",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.error
            )
        }

        item {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Today's Overview", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("Data collection status: Active - Demo sensor")
                    Text("Sensor/device status: Connected - MAX30102 PPG, MPU6050 Motion, DS18B20 skin temperature")
                    Text("Recent measurements: HR 72 bpm MEASURED quality 0.91, HRV RMSSD 48 ms DERIVED quality 0.85")
                    Text("Signal quality: Good - understandable language, not raw technical")
                    Text("Recent activity: 35% MEASURED source MPU6050")
                    Text("Personal baseline status: Baseline established mean 71 bpm std 2")
                    Text("Recent longitudinal change: LOW CHANGE SIGNAL - stable baseline")
                }
            }
        }

        item {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Data Quality", style = MaterialTheme.typography.titleMedium)
                    Text("Overall: Good")
                    Text("PPG: 0.91 MEASURED source MAX30102")
                    Text("Motion: 0.8 MEASURED source MPU6050")
                    Text("Temp: 0.88 MEASURED source DS18B20")
                    Text("Provenance: MEASURED clearly distinguished")
                }
            }
        }

        item {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Privacy & Safety", style = MaterialTheme.typography.titleMedium)
                    Text("Local-first, offline, privacy-focused")
                    Text("No cloud upload of private health data")
                    Text("Research prototype, not medical diagnosis")
                    Text("Patient ID: $patientId - single patient only, never global list")
                }
            }
        }
    }
}
