#include "handpilot_core/controller.hpp"
#include "handpilot_core/constraints.hpp"
#include "handpilot_core/inverse_kinematics.hpp"
#include "handpilot_core/planar_arm.hpp"
#include <cmath>
#include <stdexcept>
#include <utility>

namespace handpilot_core {
Controller::Controller(Config config) : config_(std::move(config)), joints_(config_.initial)
{
  if (!valid_config(config_)) {throw std::invalid_argument("invalid controller configuration");}
  requested_ = target_ = achieved();
}

Vec2 Controller::achieved() const {return forward_kinematics(config_, joints_);}

void Controller::stop(State state, const std::string & reason)
{
  state_ = state;
  reason_ = reason;
  velocity_ = {};
  active_ = false;
  requested_ = target_ = achieved();
}

void Controller::fault(const std::string & reason)
{
  rejected_ = true;
  stop(State::FAULT, reason);
}

bool Controller::observe_time(double now)
{
  if (!std::isfinite(now) || (observed_time_ && now < *observed_time_)) {
    fault("invalid or reversed steady time");
    return false;
  }
  observed_time_ = now;
  return true;
}

std::optional<double> Controller::command_age(double now) const
{
  if (!arrival_ || !std::isfinite(now) || now < *arrival_) {return std::nullopt;}
  const double age = now - *arrival_;
  return std::isfinite(age) ? std::optional<double>(age) : std::nullopt;
}

bool Controller::fresh(double now) const
{
  const auto age = command_age(now);
  return age && *age <= config_.command_timeout;
}

bool Controller::receive(const Command & command, double arrival)
{
  if (state_ == State::FAULT) {return false;}
  if (!observe_time(arrival)) {return false;}
  if (command.source_id.empty() || command.source_id.size() > 128 || !finite(command.velocity) ||
    (!command.active && (command.velocity.x != 0.0 || command.velocity.y != 0.0)))
  {
    fault("malformed command");
    return false;
  }
  if (arrival_ && command.source_id == source_ && command.sequence <= sequence_) {
    rejected_ = true;
    if (state_ == State::ENGAGED) {stop(State::HOLD, "sequence rejected");}
    else {reason_ = "sequence rejected";}
    return false;
  }
  const bool changed = command.source_id != source_;
  if (state_ == State::ENGAGED && !fresh(arrival)) {stop(State::HOLD, "command timeout");}
  if (changed && state_ == State::ENGAGED) {stop(State::HOLD, "source/session changed");}
  source_ = command.source_id;
  sequence_ = command.sequence;
  arrival_ = arrival;
  if (!command.active && state_ == State::ENGAGED) {stop(State::HOLD, "inactive input");}
  if (state_ == State::ENGAGED && !changed) {
    velocity_ = bound_velocity(command.velocity, config_.max_cartesian_speed, limited_);
    active_ = command.active;
  } else {
    velocity_ = {};
    active_ = false;
  }
  return true;
}

ActionResult Controller::set_engaged(bool engaged, double now)
{
  if (state_ == State::FAULT) {return {false, "FAULT requires explicit reset"};}
  if (!observe_time(now)) {return {false, reason_};}
  if (!engaged) {
    stop(State::HOLD, "explicit disengage");
    return {true, reason_};
  }
  if (!fresh(now)) {
    if (state_ == State::ENGAGED) {stop(State::HOLD, "command timeout");}
    return {false, "fresh command required before engagement"};
  }
  if (state_ != State::ENGAGED) {stop(State::ENGAGED, "explicit engagement; awaiting input");}
  return {true, reason_};
}

ActionResult Controller::reset()
{
  if (state_ != State::FAULT) {return {false, "reset is only valid in FAULT"};}
  if (!valid_config(config_) || !within_limits(config_, joints_)) {
    return {false, "invalid configuration or state; restart with corrected configuration"};
  }
  stop(State::DISENGAGED, "fault reset; fresh input and engagement required");
  source_.clear();
  sequence_ = 0;
  arrival_.reset();
  observed_time_.reset();
  return {true, reason_};
}

void Controller::step(double now, double dt)
{
  if (state_ == State::FAULT) {return;}
  if (!observe_time(now)) {return;}
  if (!std::isfinite(dt)) {fault("non-finite integration interval"); return;}
  if (dt <= 0.0 || dt > config_.max_dt) {
    stop(state_ == State::ENGAGED ? State::HOLD : state_, "invalid integration interval");
    return;
  }
  if (state_ != State::ENGAGED) {requested_ = target_ = achieved(); return;}
  if (!fresh(now)) {stop(State::HOLD, "command timeout"); return;}
  if (!active_ || (velocity_.x == 0.0 && velocity_.y == 0.0)) {
    requested_ = target_ = achieved();
    return;
  }
  const Vec2 origin = achieved();
  requested_ = {origin.x + velocity_.x * dt, origin.y + velocity_.y * dt};
  const auto solution = inverse_kinematics(config_, requested_, joints_);
  if (!solution.success) {
    rejected_ = true;
    target_ = origin;
    reason_ = solution.reason;
    return;
  }
  joints_ = rate_limit(config_, joints_, solution.joints, dt, limited_);
  if (!within_limits(config_, joints_)) {fault("invalid internal joint state"); return;}
  target_ = achieved();
  reason_ = limited_ ? "motion limited" : "tracking velocity";
}
}  // namespace handpilot_core
