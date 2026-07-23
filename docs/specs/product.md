# Product — boundary & intent

## The one-line promise

Ask a question of a document set and get an answer where **every claim is
traceable to a source you can open**, weak or unverifiable claims are visibly
flagged, and genuine gaps are reported rather than papered over.

## Who it's for

Anyone who needs to *trust* an answer drawn from documents: a researcher across
a pile of papers, an analyst over a set of reports, an engineer over internal
docs. The unifying need is not speed — it is being able to defend every
sentence.

## What it is

- A local-first tool: you point it at files, it builds a corpus, you ask
  questions.
- A pipeline with a hard rule at the end — nothing renders as grounded evidence
  unless it survives verification against the retrieved source text.
- Honest about its own limits: "not found in this corpus" is a first-class
  answer, not a failure.

## What it is deliberately *not* (v1)

- **Not an agent that goes and finds evidence for you.** Grounded answers over
  the corpus you give it; it does not search the web or academic databases. That
  acquisition stage is the single biggest source of complexity in the larger
  system this is drawn from, and it is out of scope here. ⏸
- **Not a planner or orchestrator.** One question, one run, no multi-step plan
  the user approves. ⏸
- **Not multi-user or a hosted service.** No accounts, no auth, single user on
  their own machine. ⏸
- **Not a summariser of summaries.** Every claim grounds out in source text, not
  in other generated text.

## The property everything serves

If a reviewer picks any sentence in an answer and asks "why should I believe
that?", the tool has a concrete response: here is the source, here is the
verbatim quote, here is the grounding tier — or here is the honest flag telling
you not to rely on it. Design choices are judged against whether they protect
that property. See [system/grounding.md](system/grounding.md).
