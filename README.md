# Decentralized Multi-Robot Fleet

A decentralized fleet-coordination framework for autonomous mobile robots, built on ROS 2 and Nav2. Every robot runs its own agent. Agents discover each other, allocate tasks through auctions, reserve shared paths, and recover from failures without a central server.

> **Status:** early development. The design below is the target; implementation is in progress and interfaces may change without notice.

## Overview

Centralized fleet managers are a single point of failure and a scaling bottleneck. This project takes the opposite approach: coordination emerges from peer-to-peer communication between robots. If one robot fails, the rest of the fleet keeps working and absorbs its tasks.

The system targets indoor logistics environments such as warehouses and factory floors, where differential-drive robots move items between stations while sharing narrow corridors.

## Key Capabilities

- **Peer discovery:** agents broadcast heartbeats and track their neighbors
- **Task auction:** robots bid on new tasks, and the best bid wins
- **Lane reservation:** robots reserve path segments before entering shared corridors
- **Deadlock handling:** circular waits are detected and resolved
- **Fault tolerance:** tasks of a lost robot return to the auction
- **Battery awareness:** robots go to charging stations when energy is low

## System Architecture

```
                 Task Source (mission generator)
                                  │  announces tasks
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
   ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
   │   Agent A   │◄───────►│   Agent B   │◄───────►│   Agent C   │
   └──────┬──────┘  peer   └──────┬──────┘  peer   └──────┬──────┘
          ▼         DDS           ▼         DDS           ▼
   ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
   │ Nav2 stack  │         │ Nav2 stack  │         │ Nav2 stack  │
   └──────┬──────┘         └──────┬──────┘         └──────┬──────┘
          ▼                       ▼                       ▼
      Robot A                 Robot B                 Robot C
```

Each robot has its own ROS 2 namespace and navigation stack. Agents talk to each other over standard ROS 2 topics, with no broker and no central coordinator.

## Repository Structure

```
decentralized-multi-robot-fleet/
├── fleet_msgs/         # Custom messages
├── fleet_agent/        # Per-robot agent
├── fleet_description/  # Robot model
├── fleet_navigation/   # Nav2 and localization configuration
├── fleet_simulation/   # Gazebo worlds
├── fleet_bringup/      # Launch files
├── fleet_tools/        # Mission generator, fault injection, metrics
├── docs/               # Design notes
└── README.md
```

## License

Apache License 2.0.

## Acknowledgments

Nav2 · slam_toolbox · robot_localization · Gazebo
