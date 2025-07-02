plugins {
    java
    application
}

group = "com.example.java"
version = "1.0.0"

java {
    sourceCompatibility = JavaVersion.VERSION_11
    targetCompatibility = JavaVersion.VERSION_11
}

repositories {
    mavenCentral()
}

dependencies {
    // Eclipse Milo OPC UA Client
    implementation("org.eclipse.milo:sdk-client:0.6.8")

    // SLF4J API
    implementation("org.slf4j:slf4j-api:1.7.36")

    // Logback Classic (SLF4J implementation)
    implementation("ch.qos.logback:logback-classic:1.5.13")
}

application {
    mainClass.set("com.example.java.Main")
}

tasks.withType<JavaCompile> {
    options.encoding = "UTF-8"
}

tasks.withType<Test> {
    useJUnitPlatform()
}
