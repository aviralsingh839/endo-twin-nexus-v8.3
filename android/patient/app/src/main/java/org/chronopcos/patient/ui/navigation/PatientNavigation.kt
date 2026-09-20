package org.chronopcos.patient.ui.navigation

/**
 * Patient Navigation - Single patient app
 * HOME, MY HEALTH, MEASUREMENTS, TIMELINE, SYMPTOMS, CYCLE, ULTRASOUND, RESULTS, REPORTS, DOCTOR SHARING, FIND CARE, EDUCATION, SETTINGS
 */

sealed class PatientScreen(val route: String, val title: String) {
    object Home : PatientScreen("home", "Home")
    object MyHealth : PatientScreen("my_health", "My Health")
    object Measurements : PatientScreen("measurements", "Measurements")
    object Timeline : PatientScreen("timeline", "Timeline")
    object Symptoms : PatientScreen("symptoms", "Symptoms")
    object Cycle : PatientScreen("cycle", "Cycle")
    object Ultrasound : PatientScreen("ultrasound", "Ultrasound")
    object Results : PatientScreen("results", "Results")
    object Reports : PatientScreen("reports", "Reports")
    object DoctorSharing : PatientScreen("doctor_sharing", "Doctor Sharing")
    object FindCare : PatientScreen("find_care", "Find Care")
    object Education : PatientScreen("education", "Education")
    object Settings : PatientScreen("settings", "Settings")

    companion object {
        val allScreens = listOf(
            Home, MyHealth, Measurements, Timeline, Symptoms, Cycle, Ultrasound, Results, Reports, DoctorSharing, FindCare, Education, Settings
        )
    }
}
