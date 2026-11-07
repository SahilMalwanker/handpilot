#include <gtest/gtest.h>
#include <cmath>
#include <limits>
#include "handpilot_core/controller.hpp"
#include "handpilot_core/constraints.hpp"

using namespace handpilot_core;

namespace {
Command input(std::uint64_t sequence, Vec2 velocity = {0.02, 0.0},
  bool active = true, const std::string & source = "session-a")
{
  return {source, sequence, velocity, active};
}

void start(Controller & controller)
{
  ASSERT_TRUE(controller.receive(input(1, {}, false), 0.0));
  ASSERT_TRUE(controller.set_engaged(true, 0.0).success);
  ASSERT_TRUE(controller.receive(input(2), 0.0));
}
}

TEST(Controller, DisengagedAndEngagementNeverAccumulate)
{
  Controller controller;
  const auto initial = controller.joints();
  EXPECT_EQ(controller.state(), State::DISENGAGED);
  EXPECT_FALSE(controller.set_engaged(true, 0.0).success);
  ASSERT_TRUE(controller.receive(input(1), 0.0));
  controller.step(0.02, 0.02);
  EXPECT_EQ(controller.joints(), initial);
  ASSERT_TRUE(controller.set_engaged(true, 0.02).success);
  controller.step(0.04, 0.02);
  EXPECT_EQ(controller.joints(), initial);
  EXPECT_DOUBLE_EQ(controller.target().x, controller.achieved().x);
  ASSERT_TRUE(controller.receive(input(2), 0.04));
  controller.step(0.06, 0.02);
  EXPECT_NE(controller.joints(), initial);
}

TEST(Controller, HoldAndReengageUseFreshTarget)
{
  Controller controller;
  start(controller);
  controller.step(0.02, 0.02);
  ASSERT_TRUE(controller.set_engaged(false, 0.02).success);
  const auto held = controller.joints();
  ASSERT_TRUE(controller.receive(input(3, {0.0, 0.12}), 0.03));
  controller.step(0.04, 0.02);
  EXPECT_EQ(controller.joints(), held);
  ASSERT_TRUE(controller.set_engaged(true, 0.04).success);
  controller.step(0.06, 0.02);
  EXPECT_EQ(controller.joints(), held);
  EXPECT_DOUBLE_EQ(controller.requested().x, controller.achieved().x);
  ASSERT_TRUE(controller.receive(input(4, {-0.02, 0.0}), 0.06));
  controller.step(0.08, 0.02);
  EXPECT_LT(controller.achieved().x, controller.requested().x + 1e-9);
  EXPECT_NE(controller.joints(), held);
}

TEST(Controller, ActiveZeroPreservesExactJointsWithoutIKRoundoff)
{
  Controller controller;
  start(controller);
  controller.step(0.02, 0.02);
  const auto held = controller.joints();
  ASSERT_TRUE(controller.receive(input(3, {}, true), 0.03));
  controller.step(0.04, 0.02);
  EXPECT_EQ(controller.state(), State::ENGAGED);
  EXPECT_EQ(controller.joints(), held);
  EXPECT_DOUBLE_EQ(controller.requested().x, controller.achieved().x);
}

TEST(Controller, StaleAndInactiveInputLatchHold)
{
  Controller controller;
  start(controller);
  controller.step(0.02, 0.02);
  const auto held = controller.joints();
  controller.step(0.26, 0.02);
  EXPECT_EQ(controller.state(), State::HOLD);
  EXPECT_EQ(controller.joints(), held);
  ASSERT_TRUE(controller.receive(input(3), 0.27));
  controller.step(0.28, 0.02);
  EXPECT_EQ(controller.state(), State::HOLD);
  EXPECT_EQ(controller.joints(), held);
  ASSERT_TRUE(controller.set_engaged(true, 0.28).success);
  ASSERT_TRUE(controller.receive(input(4, {}, false), 0.29));
  EXPECT_EQ(controller.state(), State::HOLD);
}

TEST(Controller, RecoveryBeforeTimerCannotHideTimeout)
{
  Controller controller;
  start(controller);
  ASSERT_TRUE(controller.receive(input(3), 0.26));
  EXPECT_EQ(controller.state(), State::HOLD);
  controller.step(0.27, 0.02);
  EXPECT_EQ(controller.joints(), Config{}.initial);
}

TEST(Controller, SequenceIsScopedToSessionAndDoesNotRefreshOnRejection)
{
  Controller controller;
  start(controller);
  EXPECT_FALSE(controller.receive(input(2), 0.10));
  EXPECT_EQ(controller.state(), State::HOLD);
  ASSERT_TRUE(controller.command_age(0.10));
  EXPECT_DOUBLE_EQ(*controller.command_age(0.10), 0.10);
  EXPECT_FALSE(controller.receive(input(1), 0.11));
  ASSERT_TRUE(controller.receive(input(0, {}, false, "session-b"), 0.12));
  ASSERT_TRUE(controller.set_engaged(true, 0.12).success);
  ASSERT_TRUE(controller.receive(input(1, {0.02, 0.0}, true, "session-b"), 0.12));
  controller.step(0.14, 0.02);
  const auto held = controller.joints();
  ASSERT_TRUE(controller.receive(input(100, {0.12, 0.0}, true, "session-a"), 0.15));
  EXPECT_EQ(controller.state(), State::HOLD);
  controller.step(0.16, 0.02);
  EXPECT_EQ(controller.joints(), held);
}

TEST(Controller, InvalidFiniteDtHoldsWithoutMovement)
{
  for (const double interval : {0.0, -0.01, 100.0}) {
    Controller controller;
    start(controller);
    controller.step(0.02, interval);
    EXPECT_EQ(controller.state(), State::HOLD);
    EXPECT_EQ(controller.joints(), Config{}.initial);
  }
}

TEST(Controller, SequenceWrapRequiresNewSessionAndDoesNotEngage)
{
  Controller controller;
  ASSERT_TRUE(controller.receive(input(std::numeric_limits<std::uint64_t>::max()), 0.0));
  ASSERT_TRUE(controller.set_engaged(true, 0.0).success);
  EXPECT_FALSE(controller.receive(input(0), 0.01));
  EXPECT_EQ(controller.state(), State::HOLD);
  ASSERT_TRUE(controller.receive(input(0, {}, false, "new-session"), 0.02));
  EXPECT_EQ(controller.state(), State::HOLD);
  EXPECT_EQ(controller.joints(), Config{}.initial);
}

TEST(Controller, RejectionRemainsObservableUntilPublication)
{
  Controller controller;
  EXPECT_FALSE(controller.receive(input(1, {}, false, ""), 0.0));
  ASSERT_TRUE(controller.reset().success);
  EXPECT_TRUE(controller.rejected());
  controller.clear_events();
  EXPECT_FALSE(controller.rejected());
}

TEST(Controller, NonFiniteInputAndTimeFaultAndRequireReset)
{
  for (const double invalid : {std::numeric_limits<double>::quiet_NaN(),
      std::numeric_limits<double>::infinity()})
  {
    Controller controller;
    start(controller);
    EXPECT_FALSE(controller.receive(input(3, {invalid, 0.0}), 0.01));
    EXPECT_EQ(controller.state(), State::FAULT);
    EXPECT_FALSE(controller.set_engaged(true, 0.02).success);
    EXPECT_FALSE(controller.set_engaged(false, 0.02).success);
    EXPECT_FALSE(controller.receive(input(4), 0.02));
    ASSERT_TRUE(controller.reset().success);
    EXPECT_EQ(controller.state(), State::DISENGAGED);
    EXPECT_FALSE(controller.command_age(0.02));
    EXPECT_FALSE(controller.set_engaged(true, 0.02).success);
    EXPECT_FALSE(controller.reset().success);
    ASSERT_TRUE(controller.receive(input(1), 0.02));
    ASSERT_TRUE(controller.set_engaged(true, 0.02).success);
    controller.step(0.03, invalid);
    EXPECT_EQ(controller.state(), State::FAULT);
    EXPECT_TRUE(finite(controller.joints()));
    ASSERT_TRUE(controller.reset().success);
    controller.step(invalid, 0.02);
    EXPECT_EQ(controller.state(), State::FAULT);
  }
  Controller reversed;
  ASSERT_TRUE(reversed.receive(input(1), 2.0));
  reversed.step(1.0, 0.02);
  EXPECT_EQ(reversed.state(), State::FAULT);
}

TEST(Controller, MalformedInactiveAndEmptySourceFault)
{
  Controller controller;
  EXPECT_FALSE(controller.receive(input(1, {0.1, 0.0}, false), 0.0));
  EXPECT_EQ(controller.state(), State::FAULT);
  ASSERT_TRUE(controller.reset().success);
  EXPECT_FALSE(controller.receive(input(1, {}, false, ""), 0.0));
  EXPECT_EQ(controller.state(), State::FAULT);
}

TEST(Controller, RateLimitedUpdatesDiscardTrackingError)
{
  Config config;
  config.max_speed = {0.001, 0.001};
  Controller controller(config);
  start(controller);
  auto previous = controller.joints();
  for (std::uint64_t index = 1; index <= 20; ++index) {
    const double now = static_cast<double>(index) * 0.02;
    ASSERT_TRUE(controller.receive(input(index + 2, {1.0, 0.0}), now));
    controller.step(now, 0.02);
    EXPECT_TRUE(controller.limited());
    for (std::size_t joint = 0; joint < 2; ++joint) {
      EXPECT_LE(std::abs(controller.joints()[joint] - previous[joint]), 0.00002 + 1e-12);
    }
    EXPECT_DOUBLE_EQ(controller.target().x, controller.achieved().x);
    EXPECT_DOUBLE_EQ(controller.target().y, controller.achieved().y);
    previous = controller.joints();
  }
}

TEST(Controller, UnreachableStepsCannotWindUp)
{
  Config config;
  config.initial = {0.0, 0.0};
  Controller controller(config);
  start(controller);
  for (std::uint64_t index = 1; index <= 50; ++index) {
    const double now = static_cast<double>(index) * 0.02;
    ASSERT_TRUE(controller.receive(input(index + 2, {0.12, 0.0}), now));
    controller.step(now, 0.02);
    EXPECT_TRUE(controller.rejected());
    EXPECT_EQ(controller.joints(), config.initial);
    EXPECT_NEAR(controller.requested().x, 0.5524, 1e-12);
    EXPECT_NEAR(controller.target().x, 0.55, 1e-12);
  }
  ASSERT_TRUE(controller.receive(input(100, {-0.02, 0.0}), 1.01));
  controller.step(1.02, 0.02);
  EXPECT_NE(controller.joints(), config.initial);
}
