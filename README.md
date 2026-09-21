# 🚌 Real-Time AI Bus Passenger Telemetry System

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Django](https://img.shields.io/badge/Django-6.1-092E20.svg)
![React](https://img.shields.io/badge/React-18.2-61DAFB.svg)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Computer_Vision-FF9900.svg)

A distributed, edge-to-cloud AI architecture designed to monitor bus passenger flow in real-time. This B.Tech engineering project utilizes edge computer vision to track boarding and de-boarding, synchronizes the data via a REST API, and visualizes live occupancy on a modern React dashboard.

## ✨ Key Features
* **Edge AI Tracking:** Uses YOLOv8 object detection and a mathematical virtual tripwire to accurately count passengers crossing the bus threshold.
* **REST API Synchronization:** A Django backend validates and stores telemetry data into an SQLite database with timestamp precision.
* **Live React Dashboard:** A dark-mode, glassmorphic frontend utilizing React and Recharts to display dynamic area charts and metric cards.
* **Dynamic Overload Alarms:** Features an automated, dual-redundant alert system (both on the edge video feed and the cloud UI) that visually warns the driver when bus capacity (24 seats) is exceeded.

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph Edge[Node 1: Edge AI Tracker]
        A[Camera/Video Feed] --> B(YOLOv8 Inference)
        B --> C{Virtual Tripwire Logic}
        C --> D[Calculate Occupancy]
    end

    subgraph Backend[Node 2: Django REST API]
        E(POST /api/update-telemetry) --> F[(SQLite3 Database)]
        F --> G(GET /api/get-telemetry)
    end

    subgraph Frontend[Node 3: React Dashboard]
        H[1Hz Polling Loop] --> I(React State Management)
        I --> J[Recharts AreaChart]
        I --> K[Overload CSS Trigger]
    end

    D -- "HTTP POST (JSON)" --> E
    G -- "HTTP GET (JSON)" --> H
