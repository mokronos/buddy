- Yes, that is cleaner.
     - The main reason we still rewrite card url is that the A2A JS SDK client construction path follows the card’s url
     as transport endpoint.
     - If card url points to external host, SDK may bypass Buddy proxy. So we currently rewrite it to keep traffic
     through Buddy.
     - If we refactor frontend/client bootstrap to pin endpoint to registry mountPath regardless of card url, we can
     remove that hack.

     So the cleaner target design is:

     1. Buddy registry stores canonical proxy route per agent (/a2a/<kind>/<id>).
     2. Frontend always uses registry route as transport endpoint.
     3. Card is treated as metadata, not routing authority.
     4. Proxy forwards without card-url rewriting (or only for compatibility mode).

     In short: your proposed model is right; current behavior is partly transitional compatibility glue.
