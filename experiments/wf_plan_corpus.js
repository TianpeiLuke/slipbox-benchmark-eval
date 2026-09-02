export const meta = {
  name: 'plan-corpus-full',
  description: 'Plan the remaining 32 MultiHop-RAG clusters into BB-atomic notes with block-level source assignments',
  phases: [{ title: 'Plan', detail: 'one agent per cluster: read every document, assign blocks to notes' }],
}

const REPO = '/Users/tianpeixie/github_workspace/slipbox-benchmark-eval'

// Manifest embedded rather than passed as args: args does not bind reliably
// when a workflow is resumed from scriptPath, and a silently empty manifest
// would spawn nothing while reporting success.
const CLUSTERS = [{"id": "c02", "category": "business", "publishers": ["Cnbc | World Business News Leader", "Fortune", "Globes English | Israel Business Arena", "Music Business Worldwide", "The Sydney Morning Herald"], "docs": ["doc_0097", "doc_0173", "doc_0251", "doc_0269", "doc_0557", "doc_0271", "doc_0361", "doc_0363", "doc_0380", "doc_0381", "doc_0087", "doc_0298", "doc_0485", "doc_0506", "doc_0002", "doc_0226", "doc_0536", "doc_0073", "doc_0078", "doc_0486"], "words": 32414}, {"id": "c03", "category": "business", "publishers": ["Business Line", "Business World", "Cnbc | World Business News Leader", "Globes English | Israel Business Arena", "Music Business Worldwide", "The Age", "Zee Business"], "docs": ["doc_0111", "doc_0252", "doc_0418", "doc_0133", "doc_0246", "doc_0482", "doc_0211", "doc_0212", "doc_0263", "doc_0029", "doc_0074", "doc_0217", "doc_0413", "doc_0239", "doc_0601", "doc_0375", "doc_0385", "doc_0410", "doc_0463", "doc_0027"], "words": 35363}, {"id": "c04", "category": "business", "publishers": ["Business Line", "Business Today | Latest Stock Market And Economy News India", "Business World", "Cnbc | World Business News Leader", "Financial Times", "Fortune", "Globes English | Israel Business Arena", "Iot Business News", "Music Business Worldwide", "Revyuh Media", "Seeking Alpha", "The Age", "The Guardian", "The Sydney Morning Herald", "Zee Business"], "docs": ["doc_0455", "doc_0464", "doc_0028", "doc_0085", "doc_0089", "doc_0125", "doc_0134", "doc_0182", "doc_0191", "doc_0215", "doc_0253", "doc_0302", "doc_0306", "doc_0338", "doc_0357", "doc_0373", "doc_0442", "doc_0529", "doc_0530", "doc_0532"], "words": 26798}, {"id": "c05", "category": "business", "publishers": ["Seeking Alpha"], "docs": ["doc_0581"], "words": 1271}, {"id": "c06", "category": "entertainment", "publishers": ["FOX News - Entertainment", "FOX News - Lifestyle", "Mashable", "The Age", "The Guardian", "The Sydney Morning Herald"], "docs": ["doc_0020", "doc_0171", "doc_0221", "doc_0579", "doc_0052", "doc_0284", "doc_0347", "doc_0605", "doc_0128", "doc_0130", "doc_0596", "doc_0177", "doc_0227", "doc_0348", "doc_0560", "doc_0578", "doc_0582", "doc_0000", "doc_0558", "doc_0044"], "words": 27609}, {"id": "c07", "category": "entertainment", "publishers": ["FOX News - Lifestyle", "The Independent - Life and Style"], "docs": ["doc_0045", "doc_0254", "doc_0265", "doc_0266", "doc_0280", "doc_0323", "doc_0324", "doc_0397", "doc_0502", "doc_0067", "doc_0148", "doc_0270", "doc_0393", "doc_0570", "doc_0303", "doc_0326", "doc_0388", "doc_0562", "doc_0569", "doc_0021"], "words": 22737}, {"id": "c08", "category": "entertainment", "publishers": ["Polygon"], "docs": ["doc_0055", "doc_0081", "doc_0094", "doc_0122", "doc_0123", "doc_0165", "doc_0185", "doc_0192", "doc_0213", "doc_0383", "doc_0387", "doc_0389", "doc_0428", "doc_0435", "doc_0499", "doc_0517", "doc_0533", "doc_0545", "doc_0550", "doc_0587"], "words": 56607}, {"id": "c09", "category": "entertainment", "publishers": ["Polygon"], "docs": ["doc_0236", "doc_0279", "doc_0327", "doc_0354", "doc_0382", "doc_0392", "doc_0452", "doc_0453", "doc_0462", "doc_0519", "doc_0574", "doc_0016", "doc_0017", "doc_0292", "doc_0308", "doc_0399", "doc_0434", "doc_0454", "doc_0591", "doc_0592"], "words": 34861}, {"id": "c10", "category": "entertainment", "publishers": ["BBC News - Entertainment & Arts", "FOX News - Entertainment", "FOX News - Lifestyle", "Polygon", "The Age", "The Independent - Travel", "The Sydney Morning Herald"], "docs": ["doc_0257", "doc_0543", "doc_0283", "doc_0523", "doc_0563", "doc_0586", "doc_0572", "doc_0573", "doc_0147", "doc_0154", "doc_0255", "doc_0501", "doc_0513", "doc_0555"], "words": 27736}, {"id": "c11", "category": "entertainment", "publishers": ["FOX News - Entertainment", "Polygon", "The Independent - Life and Style"], "docs": ["doc_0597", "doc_0606", "doc_0018", "doc_0036", "doc_0051", "doc_0068", "doc_0159", "doc_0174", "doc_0193", "doc_0310", "doc_0339", "doc_0358", "doc_0360", "doc_0559", "doc_0046", "doc_0070", "doc_0095", "doc_0178", "doc_0295", "doc_0019"], "words": 29925}, {"id": "c12", "category": "health", "publishers": ["FOX News - Health"], "docs": ["doc_0065", "doc_0066", "doc_0158", "doc_0163", "doc_0467", "doc_0518", "doc_0309", "doc_0390", "doc_0590", "doc_0594"], "words": 12510}, {"id": "c13", "category": "science", "publishers": ["Advanced Science News", "Eos: Earth And Space Science News", "Live Science: The Most Interesting Articles", "Science News For Students", "Scitechdaily | Science Space And Technology News 2017", "The Guardian", "Yahoo News"], "docs": ["doc_0238", "doc_0325", "doc_0604", "doc_0247", "doc_0261", "doc_0286", "doc_0466", "doc_0460", "doc_0566", "doc_0472", "doc_0556", "doc_0084", "doc_0131", "doc_0139", "doc_0233", "doc_0285", "doc_0391", "doc_0427", "doc_0436", "doc_0459"], "words": 30309}, {"id": "c14", "category": "science", "publishers": ["Yahoo News"], "docs": ["doc_0565"], "words": 1405}, {"id": "c15", "category": "sports", "publishers": ["Sporting News"], "docs": ["doc_0004", "doc_0035", "doc_0041", "doc_0062", "doc_0088", "doc_0105", "doc_0143", "doc_0167", "doc_0200", "doc_0203", "doc_0207", "doc_0225", "doc_0231", "doc_0249", "doc_0264", "doc_0273", "doc_0275", "doc_0290", "doc_0328", "doc_0368"], "words": 40737}, {"id": "c16", "category": "sports", "publishers": ["Sporting News"], "docs": ["doc_0005", "doc_0034", "doc_0040", "doc_0056", "doc_0080", "doc_0100", "doc_0103", "doc_0120", "doc_0129", "doc_0145", "doc_0187", "doc_0197", "doc_0198", "doc_0202", "doc_0204", "doc_0258", "doc_0276", "doc_0315", "doc_0317", "doc_0331"], "words": 30175}, {"id": "c17", "category": "sports", "publishers": ["Sporting News"], "docs": ["doc_0006", "doc_0037", "doc_0060", "doc_0061", "doc_0079", "doc_0114", "doc_0119", "doc_0144", "doc_0157", "doc_0180", "doc_0201", "doc_0224", "doc_0232", "doc_0288", "doc_0294", "doc_0296", "doc_0314", "doc_0341", "doc_0353", "doc_0356"], "words": 40619}, {"id": "c18", "category": "sports", "publishers": ["CBSSports.com", "Essentially Sports", "Sporting News", "Yardbarker"], "docs": ["doc_0057", "doc_0113", "doc_0179", "doc_0343", "doc_0411", "doc_0446", "doc_0577", "doc_0007", "doc_0194", "doc_0274", "doc_0344", "doc_0416", "doc_0429", "doc_0072", "doc_0183", "doc_0245", "doc_0282", "doc_0311", "doc_0395", "doc_0003"], "words": 32641}, {"id": "c19", "category": "sports", "publishers": ["CBSSports.com", "Essentially Sports", "The Guardian", "The Roar | Sports Writers Blog", "Yardbarker"], "docs": ["doc_0118", "doc_0340", "doc_0437", "doc_0515", "doc_0522", "doc_0186", "doc_0281", "doc_0297", "doc_0441", "doc_0490", "doc_0137", "doc_0146", "doc_0289", "doc_0487", "doc_0013", "doc_0092", "doc_0101", "doc_0142", "doc_0172", "doc_0244"], "words": 30849}, {"id": "c20", "category": "sports", "publishers": ["Sky Sports", "Sport Grill", "TalkSport", "The Age", "The Independent - Sports", "The New York Times", "Wide World Of Sports"], "docs": ["doc_0155", "doc_0322", "doc_0531", "doc_0166", "doc_0300", "doc_0366", "doc_0219", "doc_0425", "doc_0546", "doc_0008", "doc_0316", "doc_0012", "doc_0228", "doc_0110", "doc_0571", "doc_0209", "doc_0451", "doc_0151", "doc_0168", "doc_0208"], "words": 31150}, {"id": "c21", "category": "sports", "publishers": ["Essentially Sports", "Insidesport", "Rivals", "Sport Grill", "Sportskeeda", "TalkSport", "The Guardian", "The Independent - Sports", "The Sydney Morning Herald"], "docs": ["doc_0220", "doc_0260", "doc_0277", "doc_0307", "doc_0352", "doc_0362", "doc_0443", "doc_0445", "doc_0475", "doc_0478", "doc_0538"], "words": 15332}, {"id": "c22", "category": "sports", "publishers": ["CBSSports.com", "Essentially Sports", "The New York Times", "The Roar | Sports Writers Blog"], "docs": ["doc_0342", "doc_0438", "doc_0440", "doc_0493", "doc_0541", "doc_0561", "doc_0058", "doc_0059", "doc_0071", "doc_0149", "doc_0259", "doc_0082", "doc_0349", "doc_0423", "doc_0481", "doc_0585", "doc_0102", "doc_0108", "doc_0400", "doc_0504"], "words": 46862}, {"id": "c23", "category": "sports", "publishers": ["Sporting News", "The Guardian"], "docs": ["doc_0359", "doc_0379", "doc_0394", "doc_0432", "doc_0439", "doc_0474", "doc_0480", "doc_0484", "doc_0489", "doc_0494", "doc_0535", "doc_0554", "doc_0109", "doc_0152", "doc_0210", "doc_0330", "doc_0414", "doc_0476", "doc_0512", "doc_0542"], "words": 30916}, {"id": "c24", "category": "sports", "publishers": ["Sporting News", "The Guardian"], "docs": ["doc_0376", "doc_0386", "doc_0422", "doc_0426", "doc_0433", "doc_0447", "doc_0449", "doc_0544", "doc_0552", "doc_0553", "doc_0583", "doc_0063", "doc_0064", "doc_0093", "doc_0150", "doc_0184", "doc_0206", "doc_0242", "doc_0370", "doc_0371"], "words": 28870}, {"id": "c25", "category": "sports", "publishers": ["Sporting News", "The Roar | Sports Writers Blog"], "docs": ["doc_0378", "doc_0408", "doc_0409", "doc_0444", "doc_0483", "doc_0495", "doc_0497", "doc_0500", "doc_0534", "doc_0568", "doc_0588", "doc_0589", "doc_0022", "doc_0023", "doc_0132", "doc_0176", "doc_0240", "doc_0406", "doc_0407", "doc_0492"], "words": 41088}, {"id": "c26", "category": "technology", "publishers": ["TechCrunch"], "docs": ["doc_0015", "doc_0026", "doc_0038", "doc_0039", "doc_0042", "doc_0047", "doc_0054", "doc_0116", "doc_0124", "doc_0140", "doc_0141", "doc_0164", "doc_0181", "doc_0196", "doc_0199", "doc_0301", "doc_0304", "doc_0333", "doc_0337", "doc_0374"], "words": 27385}, {"id": "c27", "category": "technology", "publishers": ["TechCrunch"], "docs": ["doc_0033", "doc_0117", "doc_0126", "doc_0153", "doc_0160", "doc_0216", "doc_0243", "doc_0268", "doc_0318", "doc_0334", "doc_0365", "doc_0384", "doc_0398", "doc_0402", "doc_0420", "doc_0430", "doc_0469", "doc_0496", "doc_0507", "doc_0509"], "words": 22489}, {"id": "c28", "category": "technology", "publishers": ["The Verge"], "docs": ["doc_0053", "doc_0069", "doc_0083", "doc_0086", "doc_0096", "doc_0121", "doc_0127", "doc_0136", "doc_0162", "doc_0205", "doc_0235", "doc_0293", "doc_0305", "doc_0351", "doc_0364", "doc_0403", "doc_0461", "doc_0491", "doc_0521", "doc_0539"], "words": 46190}, {"id": "c29", "category": "technology", "publishers": ["Engadget", "The Verge"], "docs": ["doc_0077", "doc_0229", "doc_0234", "doc_0250", "doc_0287", "doc_0312", "doc_0313", "doc_0505", "doc_0567", "doc_0595", "doc_0090", "doc_0115", "doc_0190", "doc_0299", "doc_0346", "doc_0350", "doc_0355", "doc_0498", "doc_0575", "doc_0607"], "words": 48510}, {"id": "c30", "category": "technology", "publishers": ["Engadget", "The Age", "The Verge", "Wired"], "docs": ["doc_0170", "doc_0241", "doc_0291", "doc_0369", "doc_0424", "doc_0431", "doc_0473", "doc_0508", "doc_0548", "doc_0602", "doc_0014", "doc_0175", "doc_0319", "doc_0329", "doc_0520", "doc_0527", "doc_0600", "doc_0050", "doc_0417", "doc_0032"], "words": 50752}, {"id": "c31", "category": "technology", "publishers": ["BBC News - Technology", "Hacker News", "The Age", "The Guardian", "Wired"], "docs": ["doc_0320", "doc_0576", "doc_0076", "doc_0189", "doc_0214", "doc_0336", "doc_0345"], "words": 17365}, {"id": "c32", "category": "technology", "publishers": ["TechCrunch", "The Verge"], "docs": ["doc_0415", "doc_0450", "doc_0488", "doc_0516", "doc_0526", "doc_0547", "doc_0603", "doc_0510", "doc_0525", "doc_0540", "doc_0564", "doc_0580", "doc_0584", "doc_0048", "doc_0049", "doc_0107", "doc_0248", "doc_0372", "doc_0396", "doc_0405"], "words": 39375}, {"id": "c33", "category": "technology", "publishers": ["Engadget", "TechCrunch"], "docs": ["doc_0458", "doc_0465", "doc_0468", "doc_0511", "doc_0514", "doc_0528", "doc_0537", "doc_0549", "doc_0551", "doc_0593", "doc_0598", "doc_0599", "doc_0608", "doc_0091", "doc_0099", "doc_0104", "doc_0169", "doc_0222", "doc_0404", "doc_0524"], "words": 42916}]


const SCHEMA = {
  type: 'object',
  required: ['subplans', 'dropped', 'genre_note'],
  properties: {
    subplans: {
      type: 'array',
      items: {
        type: 'object',
        required: ['slug', 'title', 'notes'],
        properties: {
          slug: { type: 'string', description: 'lowercase_with_underscores' },
          title: { type: 'string' },
          notes: {
            type: 'array',
            items: {
              type: 'object',
              required: ['note', 'bb', 'blocks'],
              properties: {
                note: { type: 'string', description: 'filename ending .md, lowercase_with_underscores' },
                bb: { type: 'string', enum: ['concept', 'model', 'procedure', 'empirical_observation', 'argument', 'counter_argument', 'hypothesis', 'navigation'] },
                blocks: { type: 'object', additionalProperties: { type: 'array', items: { type: 'integer' } } },
              },
            },
          },
        },
      },
    },
    dropped: { type: 'object', additionalProperties: { type: 'array', items: { type: 'integer' } } },
    genre_note: { type: 'string' },
  },
}

function promptFor(cluster) {
  return `Plan the digestion of one cluster of a PUBLIC news corpus into typed atomic notes.

All paths are ABSOLUTE. Do not use relative paths — your working directory is not the repository.

REPO: ${REPO}
CLUSTER: ${cluster.id}  (category: ${cluster.category}; publishers: ${cluster.publishers.join(', ')})
DOCUMENTS (${cluster.docs.length}, ${cluster.words} words): ${cluster.docs.join(' ')}

## QUARANTINE — non-negotiable

You may read ONLY ${REPO}/data/corpus/multihop_rag/*.txt and the index.json beside them.
You must NEVER read, grep, or open ${REPO}/data/raw/multihop_rag/MultiHopRAG.json or any
file containing benchmark questions, answers, or gold labels. Those exist and are off
limits. Notes written with sight of the questions would answer them by construction and
would silently invalidate every downstream number while still looking valid.

## Step 1 — read and segment

For each document, read it in full and get its paragraph blocks with indices:

    cd ${REPO} && python3 scripts/plan_coverage.py multihop_rag --segment <doc_id>

Read the actual document text too (${REPO}/data/corpus/multihop_rag/<doc_id>.txt).
Block indices in your output MUST match the --segment numbering exactly.

## Step 2 — decompose

RULE PRECEDENCE, and the order matters:

1. TOPICAL COHERENCE GOVERNS. One note covers one subject, so retrieving it returns the
   whole of one thing rather than part of several.
2. ONE BUILDING BLOCK per note, from the closed enum. Never mix two.
3. DENSITY CONSTRAINS SIZE, it does not set boundaries. A note draws on at most 1,800
   source words. Past that, split at a sub-topic boundary — never at a word count.

Applying size before coherence is the failure to avoid: a 1,200-word newsletter roundup
is ONE document but fifteen unrelated items, and merging them gives a note retrieved for
everything that answers nothing.

Building blocks — pick by the question the content answers:
  concept               What is X?  (entities, organisations, regulations, products)
  model                 How does X relate to Y? mechanisms, causal chains
  procedure             How do I do X? ordered steps, policies with steps
  empirical_observation What happened? dated events, figures, testimony, statements
  argument              Why believe P? a claim with its grounds
  counter_argument      Why might that be wrong? rebuttals, denials, criticism
  hypothesis            Might P be true? testable prediction — RARE in news
  navigation            index only — do NOT produce these

News is dominated by empirical_observation and concept. If a building block does not
occur in these documents, DO NOT manufacture it. Absence is a finding.

## Step 3 — entity notes are shared, never duplicated

When several documents in this cluster discuss the same entity, write ONE note and give it
blocks from EACH document. That is what lets a single note satisfy several pieces of
evidence. Two near-duplicate notes split the evidence and lose both.

NEVER assign the same (doc, block) to two different notes.

## Step 4 — group into sub-plans

Group your notes into sub-plans of 4 to 15 notes each, by topical affinity. A sub-plan
producing more than 15 notes must be split further. Give each a slug and a title.

## Step 5 — drop only chrome, and list it

Do not assign: article titles (carried in the note H1), section headers, newsletter
promotion, "read more" links, contentless reaction, bylines, correction notices that add
nothing. Everything you do not assign goes in "dropped".

BUT: inspect what you drop. A block that reads like a routine correction can state the
opposite of its own headline — a scope condition on the central claim, which is exactly
what a careless summariser deletes. When in doubt, assign it.

Aim for 90%+ of each document's words assigned. Report honestly if a document is mostly
promotional and lands lower.

## Output

Return the JSON schema you were given. Note filenames are lowercase_with_underscores.md,
descriptive and specific enough to be unique across a 3,000-note vault (prefer
"twitch_partner_plus_program.md" over "program.md").`
}

phase('Plan')
const clusters = CLUSTERS
log(`planning ${clusters.length} clusters, ${clusters.reduce((a, c) => a + c.docs.length, 0)} documents`)

const results = await parallel(clusters.map(c => () =>
  agent(promptFor(c), { label: `plan:${c.id}`, phase: 'Plan', schema: SCHEMA })
    .then(r => (r ? { cluster: c.id, ...r } : { cluster: c.id, error: 'null result' }))
    .catch(e => ({ cluster: c.id, error: String(e) }))
))

const ok = results.filter(Boolean).filter(r => !r.error)
const bad = results.filter(Boolean).filter(r => r.error)
const notes = ok.reduce((a, r) => a + r.subplans.reduce((b, s) => b + s.notes.length, 0), 0)
log(`${ok.length} clusters planned, ${notes} notes; ${bad.length} failed`)
return { ok, failed: bad.map(b => b.cluster) }
