# Decentralized Multi-Robot Fleet

A decentralized fleet-coordination framework for autonomous mobile robots (AMRs), built on ROS 2 and Nav2. Every robot runs its own agent. Agents discover each other, allocate tasks through auctions, reserve shared lanes, and recover from failures with **no central server**.

![Status](https://img.shields.io/badge/status-early%20development-orange)
![ROS 2](https://img.shields.io/badge/ROS%202-Jazzy-blue)
![Nav2](https://img.shields.io/badge/Nav2-enabled-brightgreen)
![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic-orange)
![Python](https://img.shields.io/badge/Python-3.12-yellow)
![License](https://img.shields.io/badge/license-Apache--2.0-lightgrey)

> **Status: early development.** The architecture and protocols below describe the target design. Packages marked *planned* do not exist yet, and interfaces may change without notice.

---

## Overview

Centralized fleet managers are a single point of failure and a scaling bottleneck. This project takes the opposite approach: coordination emerges from peer-to-peer communication between robots. If one robot fails, the rest of the fleet keeps working and absorbs its tasks.

The system targets indoor logistics environments such as warehouses and factory floors, where differential-drive robots move items between stations while sharing narrow corridors.

## Key Capabilities

| Capability | Description |
|---|---|
| Peer discovery | Each agent broadcasts a heartbeat (ID, pose, state, battery, held resources) and maintains a live view of its neighbors. |
| Task auction | Tasks are announced to the fleet. Each eligible robot publishes a bid (path cost, battery, workload). Every agent computes the same winner independently from the same bids, so no auctioneer is needed. |
| Lane reservation | Robots reserve nodes and edges of a shared lane graph (capacity 1) before entering them, preventing head-on conflicts in corridors and intersections. |
| Deadlock handling | Circular waits are detected from heartbeats and resolved by a deterministic rule: exactly one robot yields. |
| Fault tolerance | A robot that stops sending heartbeats is declared lost, and its unfinished tasks are re-announced exactly once by the alive robot with the lowest ID. |
| Battery awareness | Idle agents route themselves to a charger when the battery falls below a threshold, and do not bid while charging. |

## System Architecture

```
                 Task Source (mission generator / WMS interface)
                                  │  /fleet/task_announce
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
   ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
   │   Agent 1   │◄───────►│   Agent 2   │◄───────►│   Agent 3   │
   │ auction     │ /fleet/*│ auction     │ /fleet/*│ auction     │
   │ reservation │   DDS   │ reservation │   DDS   │ reservation │
   │ liveness    │         │ liveness    │         │ liveness    │
   └──────┬──────┘         └──────┬──────┘         └──────┬──────┘
          ▼                       ▼                       ▼
   ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
   │ Nav2 stack  │         │ Nav2 stack  │         │ Nav2 stack  │
   │ SLAM / AMCL │         │ SLAM / AMCL │         │ SLAM / AMCL │
   └──────┬──────┘         └──────┬──────┘         └──────┬──────┘
          ▼                       ▼                       ▼
      robot_1                 robot_2                 robot_3
```

Each robot lives in its own ROS 2 namespace with its own navigation stack. The agent layer sits above Nav2 and talks to other agents over standard ROS 2 topics (DDS). There is no broker and no central coordinator.

### Agent design

All algorithmic logic lives in pure-Python classes with no ROS imports (`fleet_agent/core/`), and time is injected through a small clock abstraction. The ROS node only wires topics, timers, and actions to those classes, so the logic is unit-testable with plain `pytest`.

| Component | Responsibility |
|---|---|
| `LaneGraph` | Loads the lane graph from YAML; Dijkstra shortest path with optional blocked resources; nearest-node lookup. |
| `PeerTable` | Tracks the latest heartbeat of each peer; detects alive → lost transitions exactly once. |
| `AuctionManager` | Deterministic bid collection and winner selection (lowest cost, ties by lowest `robot_id`). |
| `ReservationManager` | Capacity-1 reservations on nodes and edges; priority by request time, ties by `robot_id`. |
| `DeadlockDetector` | Builds a wait-for graph from heartbeats and selects exactly one yielder per cycle. |
| `TaskExecutor` | Per-task state machine: go to pickup → picked up → go to dropoff → done / failed. |
| `BatteryManager` | Low-battery routing to the charger; blocks new tasks while charging. |
| `FailoverManager` | Re-announces tasks of lost peers exactly once. |

## Conventions

| Item | Convention |
|---|---|
| Robot ID | `robot_1`, `robot_2`, … (unique per robot) |
| Namespace | `/<robot_id>` |
| Frame and joint prefix | `<robot_id>_` (e.g. `robot_1_base_footprint`, `robot_1_odom`) |
| Shared frame | `map` (one per fleet) |
| Navigation action | `/<robot_id>/navigate_to_pose` (`nav2_msgs/action/NavigateToPose`) |
| Robot pose | `/<robot_id>/amcl_pose` (`geometry_msgs/msg/PoseWithCovarianceStamped`) |
| Fleet-wide topics | Global, un-namespaced, under `/fleet/` |
| Simulation time | Every launch file accepts `use_sim_time` |

### Fleet topics

| Topic | Message | Purpose |
|---|---|---|
| `/fleet/heartbeat` | `fleet_msgs/Heartbeat` | Liveness, pose, state, battery, held and awaited resources |
| `/fleet/task_announce` | `fleet_msgs/Task` | New task announcements |
| `/fleet/bids` | `fleet_msgs/Bid` | Auction bids |
| `/fleet/claims` | `fleet_msgs/Claim` | Winner claims a task |
| `/fleet/task_status` | `fleet_msgs/TaskStatus` | Assigned, picked up, done, failed, re-announced |
| `/fleet/reservations` | `fleet_msgs/Reservation` | Resource request and release |

## Repository Structure

```
decentralized-multi-robot-fleet/
├── fleet_msgs/         # Custom messages: Heartbeat, Task, Bid, Claim, TaskStatus, Reservation
├── fleet_agent/        # Per-robot agent, core algorithms, mock navigator, warehouse lane graph
├── fleet_description/  # Robot model (URDF/xacro, meshes, Gazebo sensors, spawn launch)
├── fleet_navigation/   # (planned) Nav2 and localization configuration, maps
├── fleet_simulation/   # (planned) Gazebo worlds and multi-robot scenarios
├── fleet_bringup/      # (planned) Launch files for N robots and scenarios
├── fleet_tools/        # (planned) Mission generator, fault injection, metrics collection
├── docs/               # Design notes, protocol specification, evaluation reports
└── README.md
```

### Robot model

`fleet_description` provides a differential-drive AMR with a rotating lidar and a ZED stereo camera (custom STL meshes). It is parameterized by `robot_id` and `accent_color`, so each robot in the fleet has its own namespace, prefixed frames, and a distinguishing color.

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
  ros-${ROS_DISTRO}-xacro \
  ros-${ROS_DISTRO}-rviz2
```

### Build

> Packages are implemented progressively. Commands may not work until the corresponding package exists.

```bash
mkdir -p ~/fleet_ws/src && cd ~/fleet_ws/src
git clone https://github.com/mohamedelnahas2004/decentralized-multi-robot-fleet.git
cd ~/fleet_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

### View the robot model

```bash
ros2 launch fleet_description display.launch.py robot_id:=robot_1
```

### Spawn robots in Gazebo

```bash
ros2 launch fleet_description spawn_robot.launch.py robot_id:=robot_1 x:=0.0 y:=0.0
ros2 launch fleet_description spawn_robot.launch.py robot_id:=robot_2 x:=2.0 y:=1.0 \
  accent_color:="1.0 0.5 0.0 1.0"
```

### Run the agents without Gazebo (mock navigators)

```bash
ros2 launch fleet_agent fleet_agents.launch.py robots:=3 use_mock_nav:=true
```

### Publish a task by hand

```bash
ros2 run fleet_agent publish_task --pickup <pickup_node> --dropoff <dropoff_node>
```

### Run the tests

```bash
colcon test --packages-select fleet_msgs fleet_agent
colcon test-result --verbose
```

### Full fleet simulation *(planned)*

```bash
ros2 launch fleet_bringup fleet.launch.py robots:=3 world:=warehouse.world
ros2 run fleet_tools mission_generator --rate 0.2
ros2 run fleet_tools kill_robot --id robot_2      # fault injection
```

## Evaluation

The framework is evaluated against simple baselines to quantify the benefit of decentralized allocation and reservation.

| Metric | Description |
|---|---|
| Makespan | Time to complete a fixed task set, with 1, 2, 4 and 8 robots |
| Task success rate | Percentage of tasks completed without manual intervention |
| Deadlock count | Deadlocks detected and resolved per run |
| Recovery time | Time from robot failure to task reassignment |
| Allocation strategy | Auction vs. round-robin vs. random assignment |

Results will be published in `docs/evaluation.md` as experiments are completed.

## License

Released under the Apache License 2.0. See [LICENSE](LICENSE) for details.

## Author

Mohamed Abdel Aal

## Acknowledgments

[Nav2](https://nav2.org) · [slam_toolbox](https://github.com/SteveMacenski/slam_toolbox) · [robot_localization](https://github.com/cra-ros-pkg/robot_localization) · [Gazebo](https://gazebosim.org)
