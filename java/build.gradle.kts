plugins {
    id("java")
    application
    id("com.github.johnrengelman.shadow") version "8.1.1"
}

group = "com.example.java"
version = "1.0.0"

java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}

application {
    mainClass = "com.example.java.Main"
}

repositories {
    mavenCentral()
}

dependencies {
    implementation(libs.json)
    implementation(libs.logback.classic)
    implementation(libs.milo.sdk.client)
    implementation(libs.slf4j.api)
}
