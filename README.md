# SO-101 Tire Changing Robot Arm 🏎️🤖

A small-scale, simplified version of an industrial helper arm modified for autonomous or remote-controlled tire service. This project is directly inspired by and based on [Pollen Robotics' SO-101 Arm](https://github.com/pollen-robotics/reachy-2023) architecture, customized specifically to service **1:10 scale Radio-Controlled (RC) cars**.

---

## Project Overview

Industrial robot arms are widely used in automated assembly lines and motorsports service bays. The **SO-101 Tire Changing Robot Arm** scales down this capability to a desktop size, targeting 1:10 scale RC car maintenance. 

By streamlining the kinematics and hardware footprint of the original SO-101 design, this arm achieves low-cost, precise manipulation suitable for unbolting, removing, swapping, and mounting miniature wheel assemblies.

### Key Modifications from Standard SO-101
* **Simplified Kinematics:** Motor 6 (typically dedicated to additional wrist roll/pitch degree of freedom or complex gripper rotation) has been **removed**.
* **Targeted End-Effector:** Custom socket tool / gripper interface designed specifically for standard 1:10 RC wheel hex adapters and lug nut sizes (7.2 mm).
* **Optimized Payload:** Calibration tuned for handling lightweight 1:10 scale wheels and tires.

---

## Features

* **5-DoF Operation:** Optimized 5 Degrees-of-Freedom configuration balancing payload capability and joint control simplicity.
* **Low-Cost Build:** Utilizes standard smart serial servos (e.g., Feetech STS / Dynamixel series) and 3D-printable structural components.
* **Open Source Hardware & Software:** Complete CAD files, control scripts, and kinematic models available.
* **Modular Toolhead:** Quick-change interface for switching between lug nut drivers and wheel removal grippers.

---

## Kinematics & Joint Mapping

With **Motor 6 removed**, the joint architecture is structured as follows:

| Joint ID | Name | Role / Function |
| :--- | :--- | :--- |
| **Motor 1** | Base Yaw | Rotates the arm base horizontally across the work surface. |
| **Motor 2** | Shoulder Pitch | Elevates the upper arm assembly. |
| **Motor 3** | Elbow Pitch | Extends and retracts the forearm. |
| **Motor 4** | Wrist Pitch | Adjusts vertical angle of the end-effector. |
| **Motor 5** | Wrist Roll / Tool | Rotates the lug nut socket driver or gripper orientation. |
| ~~(Motor 6)~~ | *Removed* | *Bypassed for reduced weight, simplified wiring, and lower cost.* |

---

## Getting Started

### Prerequisites

#### Hardware
* 3D Printer or 3D Printing Services (PLA+)
* 5x Compatible Smart Servos (e.g., Feetech STS3215 or equivalent depending on your build variant)
* 12V / 5A DC Power Supply
* Bus Servo Adapter Driver Board
* 1:10 Scale RC Car / 3D Printed Wheel + hex nut (CAD files found in repo)

#### Software
* Python 3.8+
* Anaconda Distribution or Miniconda
* OpenCV (optional, if using visual alignment for lug nuts)

---

## 🤝 Acknowledgments

* **[Pollen Robotics](https://www.pollen-robotics.com/):** For the original open-source SO-101 robot arm design and inspiring accessible robotics.
* The Tamiya RC Car Community

---

## 📄 License

This project is released under the [MIT License](LICENSE).
