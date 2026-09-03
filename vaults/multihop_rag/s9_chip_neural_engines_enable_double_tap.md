---
building_block: model
source_docs: [doc_0491]
---

# The S9 Chip's Neural Engines Enable Double Tap

Double tap requires the Apple Watch Series 9 and Ultra 2 because the new S9 features four neural engines for machine learning, which is what powers the gesture; on older watches, the related Assistive Touch feature ran on the main CPU. That is why double tap is unavailable on the older Apple Watches that support Assistive Touch — Series 4 or later, including the first-gen SE and Ultra — even though the gesture technically is not new.

The relation between the dedicated silicon and the outcome is quantified. "Because we're on a purpose-built part of the processor, we're not contending with all the other things the CPU is doing at any given time," says David Clark, senior director of Apple Watch software engineering; the result is that the Series 9 and Ultra 2 are 15 percent more accurate at detecting the double tap gesture, and the feature itself is much less power intensive.

The reason so much computation is needed is the noise in wrist data. At the most basic level, the algorithm that detects double tap is trained on data from the accelerometer, gyroscope, and optical heart rate sensor collected from the wrist. That is harder than it sounds: on top of calculating how light reflects off blood pumping through veins, smartwatch algorithms must account for the arm — plus muscles, veins, and tendons — physically moving during walking, running, and gesticulating, and no two people have the same body, so differences in wrist size and limb length have to be taken into consideration. Ironically, the years Apple put into improving heart rate helped cut through that noise: according to Clark, "the gaps in reliable signals for heart rate" were what his team used to confirm subtler motions like the double tap gesture. The requirement runs in both directions: "Reliability means that when you do the gesture, we're able to detect it," Clark says. "Reliability also means that when you're doing things that are almost like a tap, or a double tap, that we're not erroneously triggering the gesture. We got to make sure we're able to detect the right thing through by tuning these things with the right scenarios." So the algorithm must also differentiate when someone is in motion, the type of activity, and what other features they are using — streaming music or taking calls might seem unrelated, but the model must account for noise introduced by subsystems like LTE and Bluetooth, which is harder to do well when everything runs on the main CPU.

## Related Notes


- [AliveCor EKG Import Ban and the PTAB Patentability Ruling](alivecor_ekg_import_ban_and_the_ptab_patentability_ruling.md): also concerns Apple Watch hardware, from a different source document.
- [Anker 2-in-1 MagSafe Standby Charger Deal Listings](anker_2_in_1_magsafe_standby_charger_deal_listings.md): also concerns the Apple Watch, from a different source document.
- [Anker 3-in-1 MagSafe Charging Cube Deal Listings](anker_3_in_1_magsafe_charging_cube_deal_listings.md): also concerns the Apple Watch, from a different source document.
- [Anker 3-in-1 MagSafe Charging Dock Deal Listings](anker_3_in_1_magsafe_charging_dock_deal_listings.md): also concerns the Apple Watch, from a different source document.
- [Apple's Appeal and Stay Prospects on the Watch Ban](apple_appeal_and_stay_prospects_on_the_watch_ban.md): also concerns the Apple Watch, from a different source document.
- [Apple's Double Tap User Research And Naming](apple_double_tap_user_research_and_naming.md): same source document (doc_0491)
- [The Apple Watch Double Tap Gesture](apple_watch_double_tap_gesture.md): same source document (doc_0491)
- [AssistiveTouch Versus Double Tap](assistive_touch_versus_double_tap.md): same source document (doc_0491)
- [Double Tap's Customization Limits](double_tap_customization_limits.md): same source document (doc_0491)
- [Smartwatch Gestures And Phone Independence](smartwatch_gestures_and_phone_independence.md): same source document (doc_0491)
- [Wearable Device](term_wearable_device.md): uses the concept wearable device
- [Streaming Service](term_streaming_service.md): uses the concept streaming service
- [Wearable Fitness Tracker](term_wearable_fitness_tracker.md): uses the concept wearable fitness tracker

## Source

- doc_0491: The Verge, 2023-10-25
