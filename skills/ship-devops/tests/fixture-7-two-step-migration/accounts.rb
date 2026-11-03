class Account < ApplicationRecord
  PLANS = %w[free team enterprise].freeze

  def paid?
    plan != "free"
  end

  def self.on_plan(name)
    where(plan: name)
  end
end
