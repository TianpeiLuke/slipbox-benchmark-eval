---
tags:
  - resource
  - technology
  - model
keywords:
  - how flipboard flips publish to mastodon
  - fediverse
  - activitypub
  - magazines
  - flipboard's
  - social
topics:
  - Technology
language: markdown
date of note: 2026-09-02
status: active
building_block: model
source_docs: [doc_0507]
---

# How Flipboard "Flips" Publish To Mastodon

Under the federated design, when Flipboard users curate an article or post into one of their social magazines on Flipboard's app, with an optional comment, that "flip" will also appear as a post on their new flipboard.com Mastodon account. This is not the same server Flipboard had set up before — flipboard.social was a place to experiment with decentralized social media — because it is the Flipboard app itself that is now connected to the fediverse. Users' posts on Mastodon include a link both to the article being flipped and to the user's Flipboard magazine, while the user profile points to their Flipboard profile page.

The mapping between Flipboard identities and fediverse identities is one-to-one rather than per-magazine: as this rolls out, all Flipboard users will have one Flipboard.com account connected to the fediverse even if they host numerous Flipboard magazines. CEO Mike McCue acknowledges that this is not ideal, since their magazines may focus on different topics, but believes Mastodon could one day support a notion of sub-feeds that would allow more differentiation.

The defaults and limits are specified. Users will be able to opt out of having their flips posted on Mastodon, but being opted-in is the default experience, and the company expects to have all its user accounts connected to the fediverse by the end of January 2024. This will not impact any magazines set to "private" on Flipboard, which remain private.

## Related Notes


- [Current Fediverse Apps Mostly Clone Existing Platforms](current_fediverse_apps_mostly_clone_existing_platforms.md): overlapping coverage of Mastodon and fediverse user experience, from a different source document.
- [Decentralization As A Free Market, Not An Anti-Capitalist Project](decentralization_as_a_free_market_not_an_anti_capitalist_project.md): overlapping coverage of Mastodon and decentralized social media, from a different source document.
- [Fediverse ActivityPub Protocol](fediverse_activitypub_protocol.md): overlapping coverage of Mastodon and the fediverse, from a different source document.
- [Fediverse Definition And The Email Analogy](fediverse_definition_and_the_email_analogy.md): overlapping coverage of Flipboard, Mastodon and the fediverse, from a different source document.
- [Mastodon And X Traffic Figures](mastodon_and_x_traffic_figures.md): overlapping coverage of Mastodon's users, from a different source document.
- [Flipboard's ActivityPub Federation Launch](flipboard_activitypub_federation_launch.md): drawn from the same source document (doc_0507), the rollout this mechanism implements.
- [Flipboard Front-End Redesign Questions](flipboard_front_end_redesign_questions.md): drawn from the same source document (doc_0507), on the interface implications.
- [Flipboard's Path To The Fediverse](flipboard_path_to_the_fediverse.md): drawn from the same source document (doc_0507), on the earlier flipboard.social experiment.
- [Flipboard's Social Magazine Platform](flipboard_social_magazine_platform.md): same source document (doc_0507)
- [Mainstream Platform Adoption Of ActivityPub](mainstream_platform_adoption_of_activitypub.md): same source document (doc_0507)

## Source

- doc_0507: TechCrunch, 2023-12-18
