package org.chronopcos.doctor.ui.theme

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

/*
 * Colour roles are contrast-checked, not chosen by eye. Every content-on-
 * container pairing below meets WCAG 2.2 AA (>= 4.5:1 for text, >= 3:1 for
 * outlines and other meaningful graphics). Run
 *
 *     python scripts/diagnostics/a11y_contrast_audit.py
 *
 * after editing any value here — the audit reads this file directly and fails
 * the build if a role drops below threshold.
 */

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
    // Was #667483 (4.32:1 on surfaceVariant). Darkened to clear AA.
    onSurfaceVariant = Color(0xFF5A6875),
    // Outline bounds text fields, cards and dividers, so it needs 3:1 against
    // the surface. Was #D8E0E8 at 1.33:1 — effectively invisible.
    outline = Color(0xFF6B7785),
    // Deliberately soft tone, for decorative separators only. Never use it to
    // outline an interactive control.
    outlineVariant = Color(0xFFD8E0E8),
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
        // Generous leading keeps dense clinical text readable for low-vision
        // readers and for anyone using a large system font scale.
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

/**
 * Provenance and status colours, used as *text* on light surfaces, so each one
 * clears 4.5:1 on both surface and surfaceVariant. Status is always rendered
 * with its label text next to it — colour never carries the meaning alone.
 */
object EndoTwinSemanticColors {
    val live = Color(0xFF237A57)
    // Was #A66A00 (4.05:1 on surfaceVariant) — darkened to clear AA.
    val demo = Color(0xFF9C6200)
    val measured = Color(0xFF0B6670)
    val derived = Color(0xFF315B84)
    val model = Color(0xFF6D628A)
    // Was #667483 (4.32:1 on surfaceVariant) — matches onSurfaceVariant.
    val unavailable = Color(0xFF5A6875)
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
