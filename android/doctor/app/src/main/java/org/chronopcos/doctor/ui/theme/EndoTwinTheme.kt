package org.chronopcos.doctor.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.unit.dp

private val EndoColors = darkColorScheme(
    primary = Color(0xFF5DE3FF),
    onPrimary = Color(0xFF002B37),
    primaryContainer = Color(0xFF064D63),
    onPrimaryContainer = Color(0xFFBCEFFF),
    secondary = Color(0xFF4DE0B2),
    onSecondary = Color(0xFF00382B),
    secondaryContainer = Color(0xFF084F3E),
    onSecondaryContainer = Color(0xFFB8F5DE),
    tertiary = Color(0xFF9C8CFF),
    onTertiary = Color(0xFF24155E),
    tertiaryContainer = Color(0xFF3A2D78),
    onTertiaryContainer = Color(0xFFE7E1FF),
    background = Color(0xFF070C16),
    onBackground = Color(0xFFF3F7FC),
    surface = Color(0xFF0D1627),
    onSurface = Color(0xFFF3F7FC),
    surfaceVariant = Color(0xFF15243A),
    onSurfaceVariant = Color(0xFFA7B6CB),
    outline = Color(0xFF334866),
    error = Color(0xFFFF8091),
    errorContainer = Color(0xFF5D1C2B),
    onErrorContainer = Color(0xFFFFDCE2)
)

private val EndoTypography = Typography(
    displaySmall = Typography().displaySmall.copy(fontSize = 32.sp, fontWeight = FontWeight.Bold),
    headlineSmall = Typography().headlineSmall.copy(fontSize = 24.sp, fontWeight = FontWeight.Bold),
    titleLarge = Typography().titleLarge.copy(fontSize = 20.sp, fontWeight = FontWeight.Bold),
    titleMedium = Typography().titleMedium.copy(fontSize = 16.sp, fontWeight = FontWeight.Bold),
    bodyLarge = Typography().bodyLarge.copy(fontSize = 15.sp),
    bodyMedium = Typography().bodyMedium.copy(fontSize = 14.sp),
    labelLarge = Typography().labelLarge.copy(fontSize = 13.sp, fontWeight = FontWeight.Bold),
    labelSmall = Typography().labelSmall.copy(fontSize = 11.sp, fontWeight = FontWeight.SemiBold)
)

private val EndoShapes = Shapes(
    small = RoundedCornerShape(12.dp),
    medium = RoundedCornerShape(18.dp),
    large = RoundedCornerShape(24.dp)
)

@Composable
fun EndoTwinTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = EndoColors,
        typography = EndoTypography,
        shapes = EndoShapes,
        content = content
    )
}
