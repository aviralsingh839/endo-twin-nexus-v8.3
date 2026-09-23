package org.chronopcos.doctor.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

private val EndoColors = darkColorScheme(
    primary = Color(0xFF45D9FF),
    onPrimary = Color(0xFF032C3B),
    primaryContainer = Color(0xFF0A4057),
    onPrimaryContainer = Color(0xFFC5F3FF),
    secondary = Color(0xFF55E5B3),
    onSecondary = Color(0xFF00382C),
    secondaryContainer = Color(0xFF0A493D),
    onSecondaryContainer = Color(0xFFB9F2E1),
    tertiary = Color(0xFF887BFF),
    onTertiary = Color(0xFF21115D),
    tertiaryContainer = Color(0xFF332D68),
    onTertiaryContainer = Color(0xFFE4DEFF),
    background = Color(0xFF050D18),
    onBackground = Color(0xFFE7F1FA),
    surface = Color(0xFF0B192A),
    onSurface = Color(0xFFE7F1FA),
    surfaceVariant = Color(0xFF10243A),
    onSurfaceVariant = Color(0xFF9FB4C9),
    outline = Color(0xFF2B526F),
    error = Color(0xFFFF8E8E),
    errorContainer = Color(0xFF5B1B24),
    onErrorContainer = Color(0xFFFFDAD6)
)

private val EndoTypography = Typography(
    displaySmall = Typography().displaySmall.copy(fontSize = 34.sp, fontWeight = FontWeight.ExtraBold),
    headlineSmall = Typography().headlineSmall.copy(fontSize = 25.sp, fontWeight = FontWeight.Bold),
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
