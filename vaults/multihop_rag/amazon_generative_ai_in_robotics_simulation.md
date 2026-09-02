---
building_block: model
source_docs: [doc_0528]
---

# Generative AI In Amazon's Robotics Simulation

Tye Brady's model of where generative AI helps Amazon Robotics has two components: synthetic scene generation for simulation, and grasp affordance search — with the overall theme that generative AI has a lot of promise, particularly in influencing designers to make a better system. On the coding side, the tool suggests how to write a subroutine for a procedure or routine in real language, which you cut and paste, helping overall productivity.

For simulation, Brady says: "One example that's in my lab today is that we generate synthetic packages that are virtually indistinguishable from any picture you see. Generative AI will generate scenes, like what the robot would see with the right lighting condition. In simulation, we can pick up those generated packages with real-world contact force, all the way through with the actual perception system that's in the field. We can even damage a corner in different ways to make sure our detection algorithms are actually working the way they should." For grasp affordance — the term used for picking up an object and the orientation and pose of the end effector you want in order to grab it — the structure is combinatorial: take a set of basic primitives, give a generative AI agent all of the options that can be done with the robotic end effectors, and stitch those together in a meaningful way to determine the best method for picking. That, Brady says, ultimately helps Amazon's designers determine and algorithmically prove that was the best method.

## Related Notes

- [Amazon's Machine Learning And Generative AI Adoption](amazon_machine_learning_and_generative_ai_adoption.md): same source document; the framing that precedes these examples.
- [LLM Limits In Robot Manipulation](llm_limits_in_robot_manipulation.md): overlaps in content on picking objects and system capability, from a different source document.
- [Gemini Pro Jailbreak By Robust Intelligence](gemini_pro_jailbreak_by_robust_intelligence.md): shares generative-AI themes, from a different source document.

## Source

- doc_0528: TechCrunch, 2023-10-28
