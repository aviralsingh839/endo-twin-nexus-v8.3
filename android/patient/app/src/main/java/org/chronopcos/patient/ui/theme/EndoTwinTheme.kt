package org.chronopcos.patient.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import androidx.compose.material3.Shapes
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import androidx.compose.ui.unit.dp

private val ClinicalLightColors = lightColorScheme(
    primary = Color(0xFF0B6670),
    onPrimary = Color(0xFFFFFFFF),
    primaryContainer = Color(0xFFD9EEF0),
    onPrimaryContainer = Color(0xFF073F45),
    secondary = Color(0xFF315B84),
    onSecondary = Color(0xFFFFFFFF),
    secondaryContainer = Color(0xFFDCE7F2),
    onSecondaryContainer = Color(0xFF17344F),
    tertiary = Color(0xFF6D628A),
    onTertiary = Color(0xFFFFFFFF),
    tertiaryContainer = Color(0xFFE9E2F1),
    onTertiaryContainer = Color(0xFF3C324E),
    background = Color(0xFFF6F8FB),
    onBackground = Color(0xFF17212B),
    surface = Color(0xFFFFFFFF),
    onSurface = Color(0xFF17212B),
    surfaceVariant = Color(0xFFF0F4F7),
    onSurfaceVariant = Color(0xFF667483),
    outline = Color(0xFFD8E0E8),
    error = Color(0xFFB33A3A),
    onError = Color(0xFFFFFFFF)
)

private val ClinicalTypography = Typography().run {
    copy(
        headlineLarge = headlineLarge.copy(fontWeight = FontWeight.Bold),
        headlineMedium = headlineMedium.copy(fontWeight = FontWeight.Bold),
        headlineSmall = headlineSmall.copy(fontWeight = FontWeight.Bold),
        titleLarge = titleLarge.copy(fontWeight = FontWeight.SemiBold),
        titleMedium = titleMedium.copy(fontWeight = FontWeight.SemiBold),
        labelLarge = labelLarge.copy(fontWeight = FontWeight.SemiBold),
        bodyLarge = bodyLarge.copy(lineHeight = 24.sp),
        bodyMedium = bodyMedium.copy(lineHeight = 21.sp)
    )
}

private val ClinicalShapes = Shapes(
    extraSmall = RoundedCornerShape(4.dp),
    small = RoundedCornerShape(6.dp),
    medium = RoundedCornerShape(8.dp),
    large = RoundedCornerShape(10.dp),
    extraLarge = RoundedCornerShape(12.dp)
)

object EndoTwinSemanticColors {
    val live = Color(0xFF237A57)
    val demo = Color(0xFFA66A00)
    val measured = Color(0xFF0B6670)
    val derived = Color(0xFF315B84)
    val model = Color(0xFF6D628A)
    val unavailable = Color(0xFF667483)
    val error = Color(0xFFB33A3A)
}

@Composable
fun EndoTwinTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = ClinicalLightColors,
        typography = ClinicalTypography,
        shapes = ClinicalShapes,
        content = content
    )
}
