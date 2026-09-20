package org.chronopcos.patient.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

private val EndoColors = darkColorScheme(
    primary = Color(0xFF63D8FF),
    onPrimary = Color(0xFF003545),
    primaryContainer = Color(0xFF064B60),
    onPrimaryContainer = Color(0xFFBFEFFF),
    secondary = Color(0xFF7FE0C5),
    onSecondary = Color(0xFF00382C),
    secondaryContainer = Color(0xFF075343),
    onSecondaryContainer = Color(0xFFB9F2E1),
    tertiary = Color(0xFF9D93FF),
    onTertiary = Color(0xFF21115D),
    tertiaryContainer = Color(0xFF3A2F76),
    onTertiaryContainer = Color(0xFFE4DEFF),
    background = Color(0xFF06101D),
    onBackground = Color(0xFFE7F1FA),
    surface = Color(0xFF0B1726),
    onSurface = Color(0xFFE7F1FA),
    surfaceVariant = Color(0xFF142337),
    onSurfaceVariant = Color(0xFF9FB4C9),
    outline = Color(0xFF30455D),
    error = Color(0xFFFF8E8E),
    errorContainer = Color(0xFF5B1B24),
    onErrorContainer = Color(0xFFFFDAD6)
)

private val EndoTypography = Typography(
    displaySmall = Typography().displaySmall.copy(fontSize = 34.sp, fontWeight = FontWeight.SemiBold),
    headlineSmall = Typography().headlineSmall.copy(fontSize = 25.sp, fontWeight = FontWeight.SemiBold),
    titleLarge = Typography().titleLarge.copy(fontSize = 21.sp, fontWeight = FontWeight.SemiBold),
    titleMedium = Typography().titleMedium.copy(fontSize = 16.sp, fontWeight = FontWeight.SemiBold),
    bodyLarge = Typography().bodyLarge.copy(fontSize = 15.sp),
    bodyMedium = Typography().bodyMedium.copy(fontSize = 14.sp),
    labelLarge = Typography().labelLarge.copy(fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
)

@Composable
fun EndoTwinTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = EndoColors, typography = EndoTypography, content = content)
}
