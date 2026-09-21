package org.chronopcos.patient.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.text.font.FontWeight

/**
 * Modern patient home for ENDO-TWIN.
 *
 * Live measurements are never invented here. This build uses explicit
 * DEMO_DATA labels where illustrative values are displayed.
 */
@Composable
fun PatientHomeScreen(
    patientId: String,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.fillMaxSize()
    ) {
        LazyContent(patientId)
    }
}

@Composable
private fun LazyContent(patientId: String) {
    androidx.compose.foundation.lazy.LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(18.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item {
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                ),
                shape = MaterialTheme.shapes.large,
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier.padding(20.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Surface(
                            color = MaterialTheme.colorScheme.primary,
                            shape = RoundedCornerShape(15.dp),
                            modifier = Modifier.size(48.dp)
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(
                                    Icons.Default.AutoGraph,
                                    contentDescription = null,
                                    tint = MaterialTheme.colorScheme.onPrimary
                                )
                            }
                        }
                        Spacer(Modifier.width(12.dp))
                        Column {
                            Text("ENDO-TWIN", style = MaterialTheme.typography.labelLarge)
                            Text("Your physiological timeline", style = MaterialTheme.typography.headlineSmall)
                        }
                    }
                    Text(
                        "Patient $patientId • local-first research workspace",
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                    AssistChip(
                        onClick = {},
                        enabled = false,
                        label = { Text("DEMO_DATA • not a live record") },
                        leadingIcon = { Icon(Icons.Default.Science, null) }
                    )
                }
            }
        }

        item {
            SectionTitle("Today", "Clear separation between observation, derived features and research models.")
        }

        item {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                MetricCard("Heart rate", "72 bpm", "Illustrative only", "DEMO")
                MetricCard("HRV", "48 ms", "Pulse-derived example", "DERIVED")
            }
        }

        item {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                MetricCard("Skin temp", "32.5 °C", "Illustrative only", "DEMO")
                MetricCard("Activity", "35%", "Motion-index example", "DEMO")
            }
        }

        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = MaterialTheme.shapes.medium,
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                )
            ) {
                Column(
                    Modifier.padding(17.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.FavoriteBorder, null, tint = MaterialTheme.colorScheme.secondary)
                        Spacer(Modifier.width(9.dp))
                        Text("Data quality", style = MaterialTheme.typography.titleMedium)
                    }
                    Text(
                        "Quality gates run before research models. Missing or poor-quality data remains unavailable.",
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    QualityLine("PPG", "0.91", MaterialTheme.colorScheme.primary)
                    QualityLine("Motion", "0.80", MaterialTheme.colorScheme.secondary)
                    QualityLine("Temperature", "0.88", MaterialTheme.colorScheme.tertiary)
                }
            }
        }

        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = MaterialTheme.shapes.medium,
                colors = CardDefaults.cardColors(
                    containerColor = Color(0xFF17152B)
                )
            ) {
                Column(Modifier.padding(17.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.GraphicEq, null, tint = MaterialTheme.colorScheme.tertiary)
                        Spacer(Modifier.width(9.dp))
                        Text("VoxVasc", style = MaterialTheme.typography.titleMedium)
                        Spacer(Modifier.weight(1f))
                        Surface(
                            shape = RoundedCornerShape(50),
                            color = MaterialTheme.colorScheme.tertiaryContainer
                        ) {
                            Text(
                                "EXPERIMENTAL",
                                Modifier.padding(horizontal = 9.dp, vertical = 5.dp),
                                style = MaterialTheme.typography.labelSmall,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                    Text(
                        "Optional acoustic feature path inside CHRONO-PCOS. No hormone measurement, no standalone diagnosis.",
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        "Status: unavailable until a valid voice recording is acquired.",
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }
        }

        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = MaterialTheme.shapes.medium,
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            ) {
                Column(Modifier.padding(17.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("Personal baseline", style = MaterialTheme.typography.titleMedium)
                    Text(
                        "Not established in this session.",
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        "A baseline is learned from sufficient valid observations for this patient; it is not a population normal.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
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
private fun SectionTitle(title: String, subtitle: String) {
    Column(verticalArrangement = Arrangement.spacedBy(3.dp)) {
        Text(title, style = MaterialTheme.typography.titleLarge)
        Text(
            subtitle,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
private fun MetricCard(
    title: String,
    value: String,
    detail: String,
    provenance: String
) {
    Card(
        modifier = Modifier.weight(1f),
        shape = MaterialTheme.shapes.medium,
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(Modifier.padding(15.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(title, style = MaterialTheme.typography.labelLarge)
                Spacer(Modifier.weight(1f))
                Surface(
                    shape = RoundedCornerShape(50),
                    color = MaterialTheme.colorScheme.primaryContainer
                ) {
                    Text(
                        provenance,
                        Modifier.padding(horizontal = 7.dp, vertical = 4.dp),
                        style = MaterialTheme.typography.labelSmall
                    )
                }
            }
            Text(value, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text(detail, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun QualityLine(label: String, value: String, tint: Color) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Row {
            Text(label, style = MaterialTheme.typography.labelLarge)
            Spacer(Modifier.weight(1f))
            Text(value, color = tint, style = MaterialTheme.typography.labelLarge)
        }
        LinearProgressIndicator(
            progress = { value.toFloatOrNull()?.coerceIn(0f, 1f) ?: 0f },
            modifier = Modifier.fillMaxWidth()
        )
    }
}
