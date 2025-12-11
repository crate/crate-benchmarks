CREATE TABLE IF NOT EXISTS "doc"."tweets" (
   "data" OBJECT(DYNAMIC) AS (
      "attachments" OBJECT(DYNAMIC) AS (
         "media_keys" ARRAY(TEXT),
         "poll_ids" ARRAY(TEXT)
      ),
      "referenced_tweets" ARRAY(OBJECT(DYNAMIC) AS (
         "type" TEXT,
         "id" TEXT
      )),
      "possibly_sensitive" BOOLEAN,
      "public_metrics" OBJECT(DYNAMIC) AS (
         "like_count" BIGINT,
         "reply_count" BIGINT,
         "quote_count" BIGINT,
         "retweet_count" BIGINT,
         "impression_count" BIGINT
      ),
      "created_at" TEXT,
      "edit_controls" OBJECT(DYNAMIC) AS (
         "is_edit_eligible" BOOLEAN,
         "edits_remaining" BIGINT,
         "editable_until" TEXT
      ),
      "context_annotations" ARRAY(OBJECT(DYNAMIC) AS (
         "entity" OBJECT(DYNAMIC) AS (
            "name" TEXT,
            "id" TEXT,
            "description" TEXT
         ),
         "domain" OBJECT(DYNAMIC) AS (
            "name" TEXT,
            "description" TEXT,
            "id" TEXT
         )
      )),
      "geo" OBJECT(DYNAMIC) AS (
         "place_id" TEXT,
         "coordinates" OBJECT(DYNAMIC) AS (
            "coordinates" ARRAY(DOUBLE PRECISION),
            "type" TEXT
         )
      ),
      "entities" OBJECT(DYNAMIC) AS (
         "urls" ARRAY(OBJECT(DYNAMIC) AS (
            "display_url" TEXT,
            "images" ARRAY(OBJECT(DYNAMIC) AS (
               "width" BIGINT,
               "url" TEXT,
               "height" BIGINT
            )),
            "start" BIGINT,
            "expanded_url" TEXT,
            "unwound_url" TEXT,
            "description" TEXT,
            "end" BIGINT,
            "title" TEXT,
            "url" TEXT,
            "status" BIGINT,
            "media_key" TEXT
         )),
         "hashtags" ARRAY(OBJECT(DYNAMIC) AS (
            "start" BIGINT,
            "end" BIGINT,
            "tag" TEXT
         )),
         "mentions" ARRAY(OBJECT(DYNAMIC) AS (
            "start" BIGINT,
            "end" BIGINT,
            "id" TEXT,
            "username" TEXT
         )),
         "annotations" ARRAY(OBJECT(DYNAMIC) AS (
            "start" BIGINT,
            "normalized_text" TEXT,
            "end" BIGINT,
            "type" TEXT,
            "probability" DOUBLE PRECISION
         )),
         "cashtags" ARRAY(OBJECT(DYNAMIC) AS (
            "start" BIGINT,
            "end" BIGINT,
            "tag" TEXT
         ))
      ),
      "conversation_id" TEXT,
      "edit_history_tweet_ids" ARRAY(TEXT),
      "id" TEXT,
      "text" TEXT,
      "author_id" TEXT,
      "lang" TEXT,
      "reply_settings" TEXT,
      "in_reply_to_user_id" TEXT,
      "withheld" OBJECT(DYNAMIC) AS (
         "country_codes" ARRAY(TEXT),
         "copyright" BOOLEAN
      )
   ),
   "includes" OBJECT(DYNAMIC) AS (
      "tweets" ARRAY(OBJECT(DYNAMIC) AS (
         "referenced_tweets" ARRAY(OBJECT(DYNAMIC) AS (
            "type" TEXT,
            "id" TEXT
         )),
         "attachments" OBJECT(DYNAMIC) AS (
            "media_keys" ARRAY(TEXT),
            "poll_ids" ARRAY(TEXT)
         ),
         "possibly_sensitive" BOOLEAN,
         "public_metrics" OBJECT(DYNAMIC) AS (
            "like_count" BIGINT,
            "reply_count" BIGINT,
            "quote_count" BIGINT,
            "retweet_count" BIGINT,
            "impression_count" BIGINT
         ),
         "created_at" TEXT,
         "edit_controls" OBJECT(DYNAMIC) AS (
            "is_edit_eligible" BOOLEAN,
            "edits_remaining" BIGINT,
            "editable_until" TEXT
         ),
         "context_annotations" ARRAY(OBJECT(DYNAMIC) AS (
            "domain" OBJECT(DYNAMIC) AS (
               "name" TEXT,
               "description" TEXT,
               "id" TEXT
            ),
            "entity" OBJECT(DYNAMIC) AS (
               "name" TEXT,
               "description" TEXT,
               "id" TEXT
            )
         )),
         "geo" OBJECT(DYNAMIC) AS (
            "place_id" TEXT,
            "coordinates" OBJECT(DYNAMIC) AS (
               "coordinates" ARRAY(DOUBLE PRECISION),
               "type" TEXT
            )
         ),
         "entities" OBJECT(DYNAMIC) AS (
            "hashtags" ARRAY(OBJECT(DYNAMIC) AS (
               "start" BIGINT,
               "end" BIGINT,
               "tag" TEXT
            )),
            "mentions" ARRAY(OBJECT(DYNAMIC) AS (
               "start" BIGINT,
               "end" BIGINT,
               "id" TEXT,
               "username" TEXT
            )),
            "urls" ARRAY(OBJECT(DYNAMIC) AS (
               "display_url" TEXT,
               "images" ARRAY(OBJECT(DYNAMIC) AS (
                  "width" BIGINT,
                  "url" TEXT,
                  "height" BIGINT
               )),
               "unwound_url" TEXT,
               "description" TEXT,
               "title" TEXT,
               "status" BIGINT,
               "start" BIGINT,
               "expanded_url" TEXT,
               "end" BIGINT,
               "media_key" TEXT,
               "url" TEXT
            )),
            "annotations" ARRAY(OBJECT(DYNAMIC) AS (
               "start" BIGINT,
               "normalized_text" TEXT,
               "end" BIGINT,
               "type" TEXT,
               "probability" DOUBLE PRECISION
            )),
            "cashtags" ARRAY(OBJECT(DYNAMIC) AS (
               "start" BIGINT,
               "end" BIGINT,
               "tag" TEXT
            ))
         ),
         "conversation_id" TEXT,
         "edit_history_tweet_ids" ARRAY(TEXT),
         "id" TEXT,
         "text" TEXT,
         "author_id" TEXT,
         "lang" TEXT,
         "reply_settings" TEXT,
         "in_reply_to_user_id" TEXT,
         "withheld" OBJECT(DYNAMIC) AS (
            "country_codes" ARRAY(TEXT),
            "copyright" BOOLEAN
         )
      )),
      "users" ARRAY(OBJECT(DYNAMIC) AS (
         "pinned_tweet_id" TEXT,
         "public_metrics" OBJECT(DYNAMIC) AS (
            "tweet_count" BIGINT,
            "following_count" BIGINT,
            "listed_count" BIGINT,
            "followers_count" BIGINT
         ),
         "verified" BOOLEAN,
         "created_at" TEXT,
         "description" TEXT,
         "profile_image_url" TEXT,
         "url" TEXT,
         "protected" BOOLEAN,
         "entities" OBJECT(DYNAMIC) AS (
            "description" OBJECT(DYNAMIC) AS (
               "urls" ARRAY(OBJECT(DYNAMIC) AS (
                  "display_url" TEXT,
                  "start" BIGINT,
                  "expanded_url" TEXT,
                  "end" BIGINT,
                  "url" TEXT
               )),
               "mentions" ARRAY(OBJECT(DYNAMIC) AS (
                  "start" BIGINT,
                  "end" BIGINT,
                  "username" TEXT
               )),
               "hashtags" ARRAY(OBJECT(DYNAMIC) AS (
                  "start" BIGINT,
                  "end" BIGINT,
                  "tag" TEXT
               )),
               "cashtags" ARRAY(OBJECT(DYNAMIC) AS (
                  "start" BIGINT,
                  "end" BIGINT,
                  "tag" TEXT
               ))
            ),
            "url" OBJECT(DYNAMIC) AS (
               "urls" ARRAY(OBJECT(DYNAMIC) AS (
                  "start" BIGINT,
                  "expanded_url" TEXT,
                  "display_url" TEXT,
                  "end" BIGINT,
                  "url" TEXT
               ))
            )
         ),
         "name" TEXT,
         "location" TEXT,
         "id" TEXT,
         "username" TEXT,
         "withheld" OBJECT(DYNAMIC) AS (
            "country_codes" ARRAY(TEXT)
         )
      )),
      "media" ARRAY(OBJECT(DYNAMIC) AS (
         "duration_ms" BIGINT,
         "preview_image_url" TEXT,
         "public_metrics" OBJECT(DYNAMIC) AS (
            "view_count" BIGINT
         ),
         "width" BIGINT,
         "variants" ARRAY(OBJECT(DYNAMIC) AS (
            "content_type" TEXT,
            "bit_rate" BIGINT,
            "url" TEXT
         )),
         "type" TEXT,
         "media_key" TEXT,
         "height" BIGINT,
         "url" TEXT,
         "alt_text" TEXT
      )),
      "places" ARRAY(OBJECT(DYNAMIC) AS (
         "geo" OBJECT(DYNAMIC) AS (
            "type" TEXT,
            "properties" OBJECT(DYNAMIC),
            "bbox" ARRAY(DOUBLE PRECISION)
         ),
         "country" TEXT,
         "country_code" TEXT,
         "full_name" TEXT,
         "place_type" TEXT,
         "name" TEXT,
         "id" TEXT
      )),
      "polls" ARRAY(OBJECT(DYNAMIC) AS (
         "voting_status" TEXT,
         "options" ARRAY(OBJECT(DYNAMIC) AS (
            "votes" BIGINT,
            "position" BIGINT,
            "label" TEXT
         )),
         "id" TEXT,
         "duration_minutes" BIGINT,
         "end_datetime" TEXT
      ))
   ),
   "errors" OBJECT(DYNAMIC)
)
CLUSTERED INTO 10 SHARDS;