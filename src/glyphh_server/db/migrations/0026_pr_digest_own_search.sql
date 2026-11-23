-- PR Review Digest searched GitHub with whatever the person typed, so "Hi there" searched all of GitHub for it and
-- brought back a stranger's issue. It now always looks for the open pull requests that ask for the person's review,
-- and installed copies are brought to that: the search fixed, and no word of what "you type is used as".
UPDATE bots SET spec = (replace(spec::text,
    '"run": "github-search-issues-and-pull-requests", "input": {"query": "$input"}',
    '"run": "github-search-issues-and-pull-requests", "input": {"query": "is:pr is:open review-requested:@me"}')::jsonb)
    - 'takes' - 'try'
WHERE spec::text LIKE '%"id": "prs", "run": "github-search-issues-and-pull-requests", "input": {"query": "$input"}%';
