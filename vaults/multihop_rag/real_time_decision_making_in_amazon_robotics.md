---
building_block: model
source_docs: [doc_0528]
---

# Real-Time Decision Making In Amazon Robotics

Asked whether generative AI is useful for having robots make decisions for scenarios they haven't encountered on the fly, Tye Brady placed the capability in a longer lineage and a two-tier architecture. Real-time decision making has been part of robotics for decades, and even prior to generative AI it enabled the goods-to-person fulfillment systems Amazon had; even with Sequoia, there's real time sensing capabilities built in that can detect objects and people.

The architecture splits by latency and abstraction: the sensing needs to be in the robot, and then there's stuff Amazon holds in AWS in the cloud that has the higher level of logic. Brady attaches a scope condition to the enthusiasm — it's exciting to think about the capabilities of generative AI, but he doesn't want to get ahead of things, since Amazon Robotics always thinks in practical real-world examples. Within that limit, the approach that has worked is the same primitives-plus-stitching pattern: "we're so far pretty interested, particularly if we give primitives to our systems and then allow generative AI to stitch those together in ways that can make those real-time decisions. That has proven very useful, both in our mobility and manipulation solutions."

## Related Notes

- [Amazon Generative AI In Robotics Simulation](amazon_generative_ai_in_robotics_simulation.md): same source document; the same primitives-stitching pattern used in design and grasp planning.
- [Human-Centric Versus Humanoid Robot Design](human_centric_versus_humanoid_robot_design.md): overlaps in content on robotics mobility design, from a different source document.
- [Boston Dynamics AI Institute Research Pillars](boston_dynamics_ai_institute_research_pillars.md): overlaps in content on manipulation and mobility research, from a different source document.
- [Agility Robotics' Prediction Of Ubiquitous Humanoids](agility_robotics_prediction_of_ubiquitous_humanoids.md): overlaps in content on robot capability trajectories, from a different source document.

## Source

- doc_0528: TechCrunch, 2023-10-28
