# Transfer And Setup

All commands below are instructions for the user on the named machine, NOT RUN
by the authoring assistant. The Windows task is file authoring/inspection only.

## Before The First Build

The six `src/*/package.xml` files deliberately contain `<maintainer email="">`.
ROS manifest parsers require a real email; otherwise rosdep/colcon package discovery
can fail before compilation. In an editor, fill in a genuine maintainer contact
you authorize for these sources. Do not invent an email or borrow an unrelated
identity. The descriptive maintainer text may be updated to match that contact.
No author emails have been fabricated in Python setup metadata.

`<license>TODO</license>` and setup.py's matching field are unresolved, not a legal
grant. Choose an appropriate license and add its text before publication; do not
claim a license has already been selected. The source inspector warns about this.

## Windows To Mac To Ubuntu

1. Save all authored files in VS Code. Include hidden .github and dotfiles.
2. In File Explorer, ZIP the outer handpilot folder, so the archive has one
   handpilot directory containing src, docs, scripts, and root files.
3. Inspect archive contents. No .git, build/install/log, caches, dependencies,
   private keys, .env files, personal recordings, or nested transfer ZIPs.
4. Transfer using an approved route. No route is assumed authorized by this repo.
5. Extract on the Mac. Confirm src is directly under the extracted handpilot.
6. Review any existing Mac/VM destination before copying. Rename/stage and compare
   rather than overwrite an edited tree. Do not merge independent changes blindly.
7. If ~/handpilot does not already contain work to preserve, use this macOS command:

```bash
scp -r ~/Downloads/handpilot ubuntu-ros2:/home/sahil/
```

`ubuntu-ros2` is the existing SSH alias. `/home/sahil/handpilot` is the specified
destination; confirm it matches the SSH user's home. This is not ~/handpilot_ws.
Do not extract/copy an extra nested handpilot/handpilot workspace by accident.
ZIP need not preserve executable bits: launch files are installed as resources,
C++ executables are built, Python console scripts are installed by setup metadata.

## Ubuntu Build

Ubuntu Server 24.04 ARM64 in UTM, about 3 GB RAM/two virtual CPUs. ROS Jazzy
ros-base and ros-dev-tools are already installed. Do not rebuild ROS or install a
desktop. In a fresh build terminal source only the ROS underlay, not this half-built
workspace or the older starter overlay.

```bash
source /opt/ros/jazzy/setup.bash
cd ~/handpilot
python3 scripts/inspect_source.py
rosdep install --from-paths src --ignore-src --rosdistro jazzy -y
CMAKE_BUILD_PARALLEL_LEVEL=2 colcon build \
  --symlink-install --executor sequential
source install/setup.bash
```

If rosdep reports that it is not initialized, initialize it once using
`sudo rosdep init`, then `rosdep update --rosdistro jazzy` as the normal user.
Do not repeat initialization if its sources file already exists. Package installation
may use sudo via rosdep; builds must not. If memory is exhausted, retry a reviewed
build with `CMAKE_BUILD_PARALLEL_LEVEL=1`, retaining `--executor sequential`.
No memory footprint or build duration has been measured.

`build/`, `install/`, and `log/` are generated and ignored. Do not transfer them
between architectures or add them to source. A build failure is not resolved by
automatically sourcing the partial overlay from .bashrc.

## Run And Test

Every new run/test terminal needs both sources:

```bash
source /opt/ros/jazzy/setup.bash
source ~/handpilot/install/setup.bash
ros2 launch handpilot_bringup handpilot.launch.py
```

Separate interactive terminal, with the same environment:

```bash
ros2 run handpilot_teleop keyboard_node
```

Test terminal after build:

```bash
cd ~/handpilot
source /opt/ros/jazzy/setup.bash
source install/setup.bash
colcon test --executor sequential
colcon test-result --verbose
```

These are authored instructions, not evidence. Record actual outputs, source
identity, architecture, ROS versions, and date in [VALIDATION_STATUS](VALIDATION_STATUS.md).
