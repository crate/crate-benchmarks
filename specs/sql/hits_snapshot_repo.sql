-- Registers the local filesystem repository holding the ClickBench `hits`
-- snapshots. Used by the select/clickbench_distinct_*.toml specs, which
-- restore the table instead of re-importing the .tsv extract with COPY FROM.
--
-- Deliberately does NOT create the table: RESTORE SNAPSHOT brings its own
-- schema, shard count and settings, and fails with RelationAlreadyExists if a
-- table of that name is already present.
--
-- The node must be started with path.repo covering the location below, e.g.
--   compare_run.py -s path.repo=/home/haris/projects/crate/test-data/snapshots
-- otherwise this fails with "location [...] doesn't match any of the
-- locations specified by path.repo".
--
-- CREATE REPOSITORY has no IF NOT EXISTS, so this errors with
-- RepositoryAlreadyExistsException when run twice against the same node.
-- Fine for compare_run.py (fresh node per version); for run-spec against a
-- long-running instance, DROP REPOSITORY hits_snapshots first.
CREATE REPOSITORY hits_snapshots TYPE fs WITH (
    location = '/home/haris/projects/crate/test-data/snapshots/hits'
);
