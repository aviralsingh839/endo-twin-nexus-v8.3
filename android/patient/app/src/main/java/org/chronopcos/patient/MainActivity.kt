package org.chronopcos.patient

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.compose.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import org.chronopcos.patient.ui.theme.EndoTwinTheme

/**
 * ENDO-TWIN Patient V8.4
 *
 * Single-patient, offline-first research interface.
 * DEMO_DATA is deliberately separated from real measured/derived/clinical data.
 * CHRONO-PCOS is a disease-model module inside the broader ENDO-TWIN platform.
 */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            EndoTwinTheme {
                PatientApp(currentPatientId = "DEMO-001")
            }
        }
    }
}

private enum class PatientTab(val route: String, val label: String) {
    Home("home", "Home"),
    Health("health", "Health"),
    Measure("measure", "Measure"),
    Timeline("timeline", "Timeline"),
    Connect("connect", "Connect")
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PatientApp(currentPatientId: String) {
    val navController = rememberNavController()
    val current = navController.currentBackStackEntryAsState().value?.destination

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("ENDO-TWIN", fontWeight = FontWeight.Bold)
                        Text(
                            "Personal physiological modelling",
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                },
                actions = {
                    Surface(shape = RoundedCornerShape(50), color = MaterialTheme.colorScheme.tertiaryContainer) {
                        Text(
                            "DEMO • $currentPatientId",
                            modifier = Modifier.padding(horizontal = 12.dp, vertical = 7.dp),
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onTertiaryContainer
                        )
                    }
                    Spacer(Modifier.width(12.dp))
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background)
            )
        },
        bottomBar = {
            NavigationBar(containerColor = MaterialTheme.colorScheme.surface) {
                PatientTab.entries.forEach { tab ->
                    val selected = current?.hierarchy?.any { it.route == tab.route } == true
                    NavigationBarItem(
                        selected = selected,
                        onClick = {
                            navController.navigate(tab.route) {
                                popUpTo(navController.graph.startDestinationId) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = {
                            Icon(
                                when (tab) {
                                    PatientTab.Home -> Icons.Outlined.Home
                                    PatientTab.Health -> Icons.Outlined.FavoriteBorder
                                    PatientTab.Measure -> Icons.Outlined.MonitorHeart
                                    PatientTab.Timeline -> Icons.Outlined.Timeline
                                    PatientTab.Connect -> Icons.Outlined.Link
                                },
                                contentDescription = tab.label
                            )
                        },
                        label = { Text(tab.label) }
                    )
                }
            }
        }
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = PatientTab.Home.route,
            modifier = Modifier.padding(padding)
        ) {
            composable("home") { HomeScreen(currentPatientId) }
            composable("health") { HealthScreen(currentPatientId) }
            composable("measure") { MeasureScreen(currentPatientId) }
            composable("timeline") { TimelineScreen(currentPatientId) }
            composable("connect") { ConnectionScreen() }
        }
    }
}

@Composable
private fun SectionTitle(title: String, subtitle: String? = null) {
    Column {
        Text(title, style = MaterialTheme.typography.titleLarge)
        subtitle?.let {
            Text(it, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun ProvenanceBadge(label: String, tone: Color = MaterialTheme.colorScheme.primaryContainer) {
    Surface(shape = RoundedCornerShape(50), color = tone) {
        Text(label, modifier = Modifier.padding(horizontal = 9.dp, vertical = 5.dp), style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun MetricCard(title: String, value: String, detail: String, provenance: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
        shape = RoundedCornerShape(20.dp)
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(title, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Spacer(Modifier.weight(1f))
                ProvenanceBadge(provenance)
            }
            Text(value, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text(detail, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun DemoBanner() {
    Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF17273A)), shape = RoundedCornerShape(18.dp)) {
        Row(
            Modifier.padding(16.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.Top
        ) {
            Icon(Icons.Default.Info, null, tint = MaterialTheme.colorScheme.primary)
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("Demonstration dataset", fontWeight = FontWeight.SemiBold)
                Text(
                    "Values on this build are illustrative DEMO_DATA, not live patient measurements. Real records retain explicit provenance and quality metadata.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
private fun HomeScreen(patientId: String) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            Column(verticalArrangement = Arrangement.spacedBy(5.dp)) {
                Text("Good to see you.", style = MaterialTheme.typography.displaySmall)
                Text(
                    "Understand your physiological patterns over time.",
                    color = MaterialTheme.colorScheme.primary,
                    style = MaterialTheme.typography.bodyLarge
                )
            }
        }
        item { DemoBanner() }
        item {
            Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer), shape = RoundedCornerShape(22.dp)) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.AutoGraph, null, modifier = Modifier.size(36.dp))
                        Spacer(Modifier.width(12.dp))
                        Column {
                            Text("Personal baseline", style = MaterialTheme.typography.titleMedium)
                            Text("Illustrative learning status • not clinical certainty", style = MaterialTheme.typography.bodySmall)
                        }
                    }
                    LinearProgressIndicator(progress = 0.72f, modifier = Modifier.fillMaxWidth().height(7.dp).clip(RoundedCornerShape(50)))
                    Text("72% illustrative completeness • DEMO_DATA", style = MaterialTheme.typography.labelSmall)
                }
            }
        }
        item { SectionTitle("Today's signals", "Examples only — provenance is DEMO_DATA in this build.") }
        item { MetricCard("Heart rate", "72 bpm", "Illustrative resting-window example", "DEMO_DATA") }
        item { MetricCard("HRV • RMSSD", "48 ms", "Derived-feature example; pulse-derived HRV is not ECG", "DEMO_DATA") }
        item { MetricCard("Skin temperature", "32.5 °C", "Illustrative skin-temperature example", "DEMO_DATA") }
        item { MetricCard("Activity", "35%", "Illustrative motion/activity index", "DEMO_DATA") }
        item {
            Card(shape = RoundedCornerShape(20.dp)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Outlined.Psychology, null, tint = MaterialTheme.colorScheme.tertiary)
                        Spacer(Modifier.width(10.dp))
                        Text("CHRONO-PCOS research module", style = MaterialTheme.typography.titleMedium)
                    }
                    Text("Disease-specific research module inside ENDO-TWIN. Model outputs are not diagnoses and clinical validation is not established.")
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        ProvenanceBadge("MODEL-INFERRED", MaterialTheme.colorScheme.tertiaryContainer)
                        ProvenanceBadge("DEMO_DATA", MaterialTheme.colorScheme.secondaryContainer)
                    }
                }
            }
        }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedButton(onClick = {}, modifier = Modifier.weight(1f)) { Text("Symptoms") }
                OutlinedButton(onClick = {}, modifier = Modifier.weight(1f)) { Text("Cycle") }
            }
        }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedButton(onClick = {}, modifier = Modifier.weight(1f)) { Text("Reports") }
                OutlinedButton(onClick = {}, modifier = Modifier.weight(1f)) { Text("Settings") }
            }
        }
        item {
            Text(
                "Research / risk-screening output — not a medical diagnosis.",
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.SemiBold
            )
        }
    }
}

@Composable
private fun HealthScreen(patientId: String) {
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        item { SectionTitle("My health", "Patient-scoped workspace • $patientId") }
        item { MetricCard("Personal baseline", "72% complete", "Illustrative learning status; no clinical certainty", "DEMO_DATA") }
        item { MetricCard("Longitudinal trend", "Stable example", "Trend logic requires enough time-series observations", "DEMO_DATA") }
        item {
            Card(shape = RoundedCornerShape(20.dp)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text("How ENDO-TWIN interprets change", style = MaterialTheme.typography.titleMedium)
                    listOf("1  Personal baseline", "2  Time series and quality", "3  Change + persistence", "4  Recovery + context").forEach {
                        Text(it, style = MaterialTheme.typography.bodyMedium)
                    }
                    Text("A signal is not automatically a disease finding. Missing or low-quality data should reduce confidence rather than be filled in.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
        item {
            Card(shape = RoundedCornerShape(20.dp)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text("Provenance legend", style = MaterialTheme.typography.titleMedium)
                    listOf("MEASURED", "DERIVED", "CLINICALLY_ENTERED", "IMAGE-DERIVED", "MODEL-INFERRED", "DEMO_DATA", "UNKNOWN").forEach {
                        ProvenanceBadge(it, MaterialTheme.colorScheme.surfaceVariant)
                    }
                    Text("Every result should keep its source classification visible. UNKNOWN is a valid state.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun MeasureScreen(patientId: String) {
    var selected by remember { mutableStateOf("Overview") }
    val filters = listOf("Overview", "Signals", "Quality", "Models")
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        item { SectionTitle("Measurements", "Sensor and derived data • $patientId") }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                filters.forEach { filter ->
                    FilterChip(selected = selected == filter, onClick = { selected = filter }, label = { Text(filter) })
                }
            }
        }
        item { DemoBanner() }
        when (selected) {
            "Overview" -> {
                item { MetricCard("PPG", "20 Hz", "Illustrative MAX30102 acquisition configuration", "DEMO_DATA") }
                item { MetricCard("GSR", "Tonic + phasic", "Illustrative electrodermal signal channels", "DEMO_DATA") }
                item { MetricCard("Motion", "IMU", "Illustrative MPU6050 activity channel", "DEMO_DATA") }
                item { MetricCard("Temperature", "Skin trend", "Illustrative DS18B20 channel", "DEMO_DATA") }
            }
            "Signals" -> item {
                Card(shape = RoundedCornerShape(20.dp)) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("Signal pipeline", style = MaterialTheme.typography.titleMedium)
                        Text("Raw acquisition → quality control → filtering → feature extraction → longitudinal context")
                        Text("No values are synthesized into real patient records. Long gaps remain missing.")
                    }
                }
            }
            "Quality" -> item {
                Card(shape = RoundedCornerShape(20.dp)) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("Data quality", style = MaterialTheme.typography.titleMedium)
                        Text("Sensor quality should be reported per channel and carried into downstream model uncertainty.")
                        LinearProgressIndicator(progress = 0.91f, modifier = Modifier.fillMaxWidth())
                        Text("Illustrative quality: 0.91 • DEMO_DATA")
                    }
                }
            }
            "Models" -> item {
                Card(shape = RoundedCornerShape(20.dp)) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("Research-model separation", style = MaterialTheme.typography.titleMedium)
                        Text("Observed data and model-inferred output are displayed as separate layers.")
                        ProvenanceBadge("MODEL-INFERRED", MaterialTheme.colorScheme.tertiaryContainer)
                    }
                }
            }
        }
    }
}

@Composable
private fun TimelineScreen(patientId: String) {
    val events = listOf(
        "Sensor session" to "DEMO_DATA • illustrative session • 19 Sep 2026",
        "Symptom entry" to "CLINICALLY_ENTERED • example user entry • 18 Sep 2026",
        "Cycle event" to "CLINICALLY_ENTERED • example event • 15 Sep 2026",
        "Ultrasound study" to "IMAGE-DERIVED • unsupported anatomical features remain UNKNOWN",
        "Model run" to "MODEL-INFERRED • research output • not diagnosis",
        "Report" to "Report generated • provenance retained"
    )
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { SectionTitle("Health timeline", "Chronological, patient-scoped • $patientId") }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                AssistChip(onClick = {}, label = { Text("All events") }, leadingIcon = { Icon(Icons.Default.FilterList, null) })
                AssistChip(onClick = {}, label = { Text("2026") })
            }
        }
        items(events) { (title, detail) ->
            Card(shape = RoundedCornerShape(18.dp)) {
                Row(Modifier.padding(16.dp), verticalAlignment = Alignment.Top) {
                    Box(Modifier.size(12.dp).clip(RoundedCornerShape(50)).background(MaterialTheme.colorScheme.primary))
                    Spacer(Modifier.width(14.dp))
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text(title, style = MaterialTheme.typography.titleMedium)
                        Text(detail, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
        }
    }
}


@Composable
private fun ConnectionScreen() {
    val scope=rememberCoroutineScope()
    var endpoint by remember { mutableStateOf("") }
    var code by remember { mutableStateOf("") }
    var status by remember { mutableStateOf("Not connected") }
    var detail by remember { mutableStateOf("Start Doctor Workstation on the same Wi-Fi. Open Mobile Link to see its address and 6-digit code.") }
    var token by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    fun request(action:suspend()->String){
        if(busy)return
        busy=true
        scope.launch {
            try{
                val json=JSONObject(action())
                if(json.optBoolean("paired",false)){
                    token=json.optString("token").takeIf{it.isNotBlank()}
                    status="Connected"
                    detail="Paired to "+json.optString("server_name","ENDO-TWIN Workstation")+"."
                }else{
                    status=json.optString("status","Completed")
                    detail=json.optString("message","Request completed.")
                }
            }catch(e:Exception){
                status="Connection failed"
                detail=e.message ?: "Check Wi-Fi, address, code and firewall."
            }finally{busy=false}
        }
    }
    LazyColumn(Modifier.fillMaxSize(),contentPadding=PaddingValues(20.dp),verticalArrangement=Arrangement.spacedBy(14.dp)){
        item{SectionTitle("Connect to a workstation","Local Wi-Fi pairing • no cloud account required")}
        item{
            Card(shape=RoundedCornerShape(22.dp),colors=CardDefaults.cardColors(
                containerColor=if(status=="Connected") MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant
            )){
                Column(Modifier.padding(18.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){
                    Row(verticalAlignment=Alignment.CenterVertically){
                        Icon(if(status=="Connected") Icons.Default.Link else Icons.Default.Wifi,null,tint=MaterialTheme.colorScheme.primary,modifier=Modifier.size(30.dp))
                        Spacer(Modifier.width(12.dp))
                        Column{
                            Text(status,style=MaterialTheme.typography.titleLarge,fontWeight=FontWeight.Bold)
                            Text("ENDO-TWIN local bridge",style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                    Text(detail)
                    Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){
                        ProvenanceBadge("LOCAL NETWORK",MaterialTheme.colorScheme.secondaryContainer)
                        ProvenanceBadge(if(token==null)"PAIRING REQUIRED" else "PAIRED",MaterialTheme.colorScheme.tertiaryContainer)
                    }
                }
            }
        }
        item{OutlinedTextField(value=endpoint,onValueChange={endpoint=it},modifier=Modifier.fillMaxWidth(),label={Text("Workstation address")},placeholder={Text("192.168.1.20:7777")},singleLine=true,supportingText={Text("Use Doctor Workstation → Mobile Link.")})}
        item{OutlinedTextField(value=code,onValueChange={v->code=v.filter(Char::isDigit).take(6)},modifier=Modifier.fillMaxWidth(),label={Text("6-digit pairing code")},placeholder={Text("123456")},singleLine=true)}
        item{
            Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(10.dp)){
                Button(onClick={request{postJson(endpointFor(endpoint,"/v1/pair"),JSONObject().put("code",code).toString())}},modifier=Modifier.weight(1f),enabled=!busy&&endpoint.isNotBlank()&&code.length==6){Text("Pair")}
                OutlinedButton(onClick={request{getJson(endpointFor(endpoint,"/v1/health"))}},modifier=Modifier.weight(1f),enabled=!busy&&endpoint.isNotBlank()){Text("Test")}
            }
        }
        item{
            Card(shape=RoundedCornerShape(20.dp)){
                Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(8.dp)){
                    Text("Send a deliberate session package",style=MaterialTheme.typography.titleMedium)
                    Text("This build sends DEMO_DATA only. Production transfer should populate from the local patient repository and retain provenance.",style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
                    Button(onClick={
                        val t=token
                        if(t==null){status="Pair first";detail="Enter the workstation address and code, then press Pair.";return@Button}
                        request{
                            val payload=JSONObject().put("schema_version","1.0").put("source_app","ENDO-TWIN Patient Android").put("patient_id","DEMO-001").put("label","DEMO_DATA").put("provenance","DEMO_DATA").put("created_at_epoch_ms",System.currentTimeMillis())
                                .put("measurements",JSONObject().put("heart_rate_bpm",72).put("hrv_rmssd_ms",48).put("skin_temperature_c",32.5).put("activity_index",35))
                                .put("note","Demonstration payload only; not a clinical record.")
                            postJson(endpointFor(endpoint,"/v1/upload"),payload.toString(),t)
                        }
                    },modifier=Modifier.fillMaxWidth(),enabled=!busy&&token!=null){Text("Send latest session")}
                }
            }
        }
        item{Text("Security boundary: trusted LAN research bridge only. Pairing is not production authentication, authorization, encryption or clinical security.",style=MaterialTheme.typography.labelSmall,color=MaterialTheme.colorScheme.error)}
        item{Text("Research / risk-screening output — not a medical diagnosis.",color=MaterialTheme.colorScheme.error,style=MaterialTheme.typography.labelMedium,fontWeight=FontWeight.SemiBold)}
    }
}
private fun endpointFor(raw:String,path:String):String{val v=raw.trim().trimEnd('/');val base=if(v.startsWith("http://")||v.startsWith("https://"))v else "http://"+v;return base+path}
private suspend fun getJson(url:String):String=withContext(Dispatchers.IO){
    val c=(URL(url).openConnection() as HttpURLConnection).apply{requestMethod="GET";connectTimeout=5000;readTimeout=5000;useCaches=false}
    try{val r=c.responseCode;val s=if(r in 200..299)c.inputStream else c.errorStream;val b=s?.bufferedReader()?.use{it.readText()}.orEmpty();if(r !in 200..299)error("HTTP "+r+": "+b);b}finally{c.disconnect()}
}
private suspend fun postJson(url:String,body:String,token:String?=null):String=withContext(Dispatchers.IO){
    val c=(URL(url).openConnection() as HttpURLConnection).apply{requestMethod="POST";connectTimeout=5000;readTimeout=5000;doOutput=true;useCaches=false;setRequestProperty("Content-Type","application/json");token?.let{setRequestProperty("X-Endo-Token",it)}}
    try{c.outputStream.use{it.write(body.toByteArray(Charsets.UTF_8))};val r=c.responseCode;val s=if(r in 200..299)c.inputStream else c.errorStream;val b=s?.bufferedReader()?.use{it.readText()}.orEmpty();if(r !in 200..299)error("HTTP "+r+": "+b);b}finally{c.disconnect()}
}
@Composable
private fun CareScreen() {
    val providers = listOf(
        "Demo Women's Health Clinic" to "DEMO DIRECTORY • Gynecology • distance illustrative 1.2 km",
        "Demo Diagnostic Centre" to "DEMO DIRECTORY • Laboratory • distance illustrative 2.1 km",
        "Demo Supplies Provider" to "DEMO DIRECTORY • Health supplies • availability not verified"
    )
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        item { SectionTitle("Find care", "Accessibility layer • real-world availability is not represented") }
        item { DemoBanner() }
        items(providers) { (name, detail) ->
            Card(shape = RoundedCornerShape(20.dp)) {
                Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Outlined.LocationOn, null, tint = MaterialTheme.colorScheme.primary)
                    Spacer(Modifier.width(12.dp))
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text(name, style = MaterialTheme.typography.titleMedium)
                        Text(detail, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    TextButton(onClick = {}) { Text("View") }
                }
            }
        }
        item {
            Text("Demo directory only • do not treat provider names, distance, hours, verification, or availability as live information.", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.error)
        }
    }
}
