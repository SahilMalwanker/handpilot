#pragma once

#include <optional>
#include "handpilot_core/types.hpp"

namespace handpilot_core {
class Controller {
public:
  explicit Controller(Config config = {});
  bool receive(const Command & command, double arrival);
  ActionResult set_engaged(bool engaged, double now);
  ActionResult reset();
  void step(double now, double dt);
  void fault(const std::string & reason);
  std::optional<double> command_age(double now) const;
  State state() const {return state_;}
  const Joints & joints() const {return joints_;}
  Vec2 achieved() const;
  Vec2 requested() const {return requested_;}
  Vec2 target() const {return target_;}
  const std::string & reason() const {return reason_;}
  bool limited() const {return limited_;}
  bool rejected() const {return rejected_;}
  void clear_events() {limited_ = false; rejected_ = false;}

private:
  bool observe_time(double now);
  bool fresh(double now) const;
  void stop(State state, const std::string & reason);
  Config config_;
  State state_{State::DISENGAGED};
  Joints joints_;
  Vec2 requested_;
  Vec2 target_;
  Vec2 velocity_;
  bool active_{false};
  bool limited_{false};
  bool rejected_{false};
  std::string reason_{"startup: explicit engagement required"};
  std::string source_;
  std::uint64_t sequence_{0};
  std::optional<double> arrival_;
  std::optional<double> observed_time_;
};
}  // namespace handpilot_core
