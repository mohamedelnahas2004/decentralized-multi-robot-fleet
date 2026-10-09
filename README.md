# Decentralized Multi-Robot Fleet

A decentralized fleet-coordination framework for autonomous mobile robots, built on ROS 2 and Nav2. Every robot runs its own agent. Agents discover each other, allocate tasks through auctions, reserve shared paths, and recover from failures without a central server.

> **Status: Early development.** The architecture and protocols below describe the target design. Implementation is in progress, and the [Roadmap](#roadmap) shows exactly what is done and what is planned. Interfaces may change without notice.

![Status](https://img.shields.io/badge/status-early_development-orange)
![ROS 2 Jazzy](https://img.shields.io/badge/ROS_2-Jazzy-22314E)
![Nav2](https://img.shields.io/badge/Nav2-enabled-blue)
![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic-orange)
![Python](https://img.shields.io/badge/Python-3.12-yellow)
![License](https://img.shields.io/badge/License-Apache--2.0-green)

---

## Overview

Centralized fleet managers are a single point of failure and a scaling bottleneck. This project takes the opposite approach: coordination emerges from peer-to-peer communication between robots. If one robot fails, the rest of the fleet keeps working and absorbs its tasks.

The system targets indoor logistics environments such as warehouses and factory floors, where a fleet of differential-drive robots must move items between stations while sharing narrow corridors.

## Key Capabilities

| Capability | Description |
|---|---|
| **Peer discovery** | Each agent broadcasts a heartbeat (ID, pose, state, battery) and maintains a live view of its neighbors. |
| **Task auction** | New tasks are announced to the fleet. Robots submit bids based on distance, battery level and current workload; the best bid wins. |
| **Lane reservation** | Robots reserve segments of a shared lane graph before entering them, preventing head-on conflicts in corridors and intersections. |
| **Deadlock handling** | Circular waits between robots are detected and resolved with a deterministic priority rule. |
| **Fault tolerance** | A robot that stops sending heartbeats is declared lost, and its unfinished tasks return to the auction. |
| **Battery awareness** | Agents route themselves to charging stations when energy drops below a threshold. |

## System Architecture

```
                 Task Source (mission generator / WMS interface)
                                  │  announces tasks
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
   ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
   │   Agent A   │◄───────►│   Agent B   │◄───────►│   Agent C   │
   │ auction     │  peer   │ auction     │  peer   │ auction     │
   │ reservation │  DDS    │ reservation │  DDS    │ reservation │
   │ liveness    │         │ liveness    │         │ liveness    │
   └──────┬──────┘         └──────┬──────┘         └──────┬──────┘
          ▼                       ▼                       ▼
   ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
   │ Nav2 stack  │         │ Nav2 stack  │         │ Nav2 stack  │
   │ SLAM / AMCL │         │ SLAM / AMCL │         │ SLAM / AMCL │
   └──────┬──────┘         └──────┬──────┘         └──────┬──────┘
          ▼                       ▼                       ▼
      Robot A                 Robot B                 Robot C
```

Each robot is isolated in its own ROS 2 namespace with its own TF tree and navigation stack. The agent layer sits above Nav2 and communicates with other agents over standard ROS 2 topics (DDS). There is no broker and no central coordinator.

## Agent Responsibilities

Each agent is a single ROS 2 node that owns four concerns:

1. **Liveness.** Publish and monitor heartbeats; maintain the neighbor table.
2. **Allocation.** Participate in task auctions, compute bids, and execute won tasks through Nav2.
3. **Traffic.** Request and release lane reservations; detect and break deadlocks.
4. **Recovery.** Re-announce tasks abandoned by lost peers; handle charging and local faults.

## Repository Structure

```
decentralized-multi-robot-fleet/
├── fleet_agent/        # Per-robot agent: liveness, auction, reservations, recovery
├── fleet_msgs/         # Custom messages: Heartbeat, Task, Bid, Claim, Reservation
├── fleet_navigation/   # Nav2 and localization configuration, maps, lane graphs
├── fleet_simulation/   # Gazebo worlds, robot models, multi-robot spawning
├── fleet_bringup/      # Launch files for N robots and scenarios
├── fleet_tools/        # Mission generator, fault injection, metrics collection
├── docs/               # Design notes, protocol specification, evaluation reports
└── README.md
```

## Getting Started

### Prerequisites

- Ubuntu 24.04
- ROS 2 Jazzy
- Gazebo Harmonic
- Nav2, slam_toolbox, robot_localization

```bash
sudo apt install -y \
  ros-${ROS_DISTRO}-navigation2 \
  ros-${ROS_DISTRO}-nav2-bringup \
  ros-${ROS_DISTRO}-slam-toolbox \
  ros-${ROS_DISTRO}-robot-localization \
  ros-${ROS_DISTRO}-ros-gz \
  ros-${ROS_DISTRO}-gz-ros2-control \
  ros-${ROS_DISTRO}-xacro \
  ros-${ROS_DISTRO}-rviz2
```

### Build

> Note: the packages and launch files referenced below are being implemented progressively. Commands may not work until the corresponding roadmap item is checked.

```bash
mkdir -p ~/fleet_ws/src && cd ~/fleet_ws/src
git clone https://github.com/<your-username>/decentralized-multi-robot-fleet.git
cd ~/fleet_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

### Run a Simulation

```bash
# Launch a fleet of 3 robots in the warehouse world
ros2 launch fleet_bringup fleet.launch.py robots:=3 world:=warehouse.world

# Start generating tasks
ros2 run fleet_tools mission_generator --rate 0.2
```

### Fault Injection

```bash
# Simulate a robot failure and observe task reallocation
ros2 run fleet_tools kill_robot --id robot_2
```

## Evaluation

The framework is evaluated against simple baselines to quantify the benefit of decentralized allocation and reservation.

| Metric | Description |
|---|---|
| Makespan | Time to complete a fixed task set, with 1, 2, 4 and 8 robots |
| Task success rate | Percentage of tasks completed without manual intervention |
| Deadlock count | Number of deadlocks detected and resolved per run |
| Recovery time | Time from robot failure to task reassignment |
| Allocation strategy | Auction vs. round-robin vs. random assignment |

Results will be published in `docs/evaluation.md` as experiments are completed.

## Roadmap

Current phase: **planning and single-robot baseline.** Checked items are complete; everything else is planned.

- [ ] Single-robot baseline: Nav2 with SLAM and AMCL
- [ ] Multi-robot simulation with isolated namespaces and TF prefixes
- [ ] Agent node: heartbeat and neighbor table
- [ ] Task auction and mission generator
- [ ] Lane graph and reservation protocol
- [ ] Deadlock detection and resolution
- [ ] Fault injection and task recovery
- [ ] Charging behavior
- [ ] Benchmark suite and evaluation report
- [ ] Hardware deployment on differential-drive robots

## Contributing

1. Create a branch named `<author>/<topic>`.
2. Make focused commits with clear messages.
3. Open a pull request and request a review.
4. Merge after approval using squash-merge.

Please include tests or a reproducible scenario with any behavioral change.

## Team

| Name | Area |
|---|---|
| _Name_ | Localization and mapping |
| _Name_ | Fleet coordination |
| _Name_ | Simulation and infrastructure |

## License

Released under the Apache License 2.0. See [LICENSE](LICENSE) for details.

## Acknowledgments

[Nav2](https://nav2.org/) · [slam_toolbox](https://github.com/SteveMacenski/slam_toolbox) · [robot_localization](https://github.com/cra-ros-pkg/robot_localization) · [ros2_control](https://control.ros.org/) · [Gazebo](https://gazebosim.org/)
