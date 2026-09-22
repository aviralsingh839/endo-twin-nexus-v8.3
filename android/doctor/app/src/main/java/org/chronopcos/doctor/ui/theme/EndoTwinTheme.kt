package org.chronopcos.doctor.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

private val EndoColors = darkColorScheme(
    primary = Color(0xFF63D8C3),
    onPrimary = Color(0xFF06211D),
    primaryContainer = Color(0xFF173E3B),
    onPrimaryContainer = Color(0xFFB9F4E6),
    secondary = Color(0xFFA9B7FF),
    onSecondary = Color(0xFF202743),
    secondaryContainer = Color(0xFF353D64),
    onSecondaryContainer = Color(0xFFDCE2FF),
    tertiary = Color(0xFFF2B56B),
    onTertiary = Color(0xFF30220F),
    tertiaryContainer = Color(0xFF58401E),
    onTertiaryContainer = Color(0xFFFFDFAB),
    background = Color(0xFF151821),
    onBackground = Color(0xFFECEFF5).copy(),
    surface = Color(0xFF1D222D),
    onSurface = Color(0xFFECEFF5).copy(),
    surfaceVariant = Color(0xFF252B38),
    onSurfaceVariant = Color(0xFFA4ADBF),
    outline = Color(0xFF3A4355),
    error = Color(0xFFFF8A7B),
    errorContainer = Color(0xFF512A2A),
    onErrorContainer = Color(0xFFFFDAD5)
)

private val EndoTypography = Typography(
    displayLarge = Typography().displayLarge.copy(fontSize = 36.sp, fontWeight = FontWeight.SemiBold),
    displaySmall = Typography().displaySmall.copy(fontSize = 32.sp, fontWeight = FontWeight.SemiBold),
    headlineMedium = Typography().headlineMedium.copy(fontSize = 26.sp, fontWeight = FontWeight.SemiBold),
    headlineSmall = Typography().headlineSmall.copy(fontSize = 23.sp, fontWeight = FontWeight.SemiBold),
    titleLarge = Typography().titleLarge.copy(fontSize = 20.sp, fontWeight = FontWeight.SemiBold),
    titleMedium = Typography().titleMedium.copy(fontSize = 16.sp, fontWeight = FontWeight.SemiBold),
    bodyLarge = Typography().bodyLarge.copy(fontSize = 15.sp),
    bodyMedium = Typography().bodyMedium.copy(fontSize = 14.sp),
    labelLarge = Typography().labelLarge.copy(fontSize = 13.sp, fontWeight = FontWeight.SemiBold),
    labelSmall = Typography().labelSmall.copy(fontSize = 10.sp, fontWeight = FontWeight.SemiBold)
)

@Composable
fun EndoTwinTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = EndoColors, typography = EndoTypography, content = content)
}
