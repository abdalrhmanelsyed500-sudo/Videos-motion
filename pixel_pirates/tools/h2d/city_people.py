"""CP-1 revision: who lives in the capital. Every speaker is a man (project rule 1); no religion, no sexual content (rules 2, 3).
Shop and office texts are keyed by building; names come from a pool, in a fixed order, so the data is deterministic."""
from __future__ import annotations

NAMES = ["Edmund Pike", "Josiah Mott", "Tobias Wren", "Hartley Brine", "Cedric Marl", "Nathaniel Shaw", "Obadiah Fenn", "Lucas Harrow",
         "Matthias Orne", "Silvan Drake", "Rupert Hale", "Barnard Quill", "Gideon Marsh", "Alaric Thorne", "Wilfred Coombe", "Jasper Lowe",
         "Ambrose Keel", "Benedict Rook", "Cornelius Vane", "Dunstan Pell", "Ezra Tallow", "Fergus Dunne", "Godfrey Blythe", "Hobart Finch",
         "Ignatius Moor", "Jarvis Wick", "Kendrick Ash", "Leopold Strand", "Mortimer Gale", "Nigel Sparrow", "Osmund Reeve", "Percival Hobb",
         "Quentin Bell", "Roland Fisk", "Sebastian Crane", "Thaddeus Rudd", "Ulric Penn", "Valentine Rusk", "Warren Tidd", "Xavier Lunt",
         "Yorick Stone", "Zachary Dyer", "Abel Garnet", "Bram Sutter", "Conrad Weir", "Dermot Kane", "Elias Ward", "Felix Hartwell"]

SHOPS = {
    "shop_baker": ("Baker", "Warm loaves, Captain! Still steaming.", "Bread today, biscuit for the voyage. A hungry crew is a short crew.",
                   "Loaves, ship's biscuit by the sack, honey cake."),
    "shop_chandler": ("Chandler", "Rope, tar, lamp oil. If it floats or burns, I have it.", "A sloop needs spare line. Everyone forgets until the wind is up.",
                      "Rope, tar, lamp oil, tallow, blocks and tackle."),
    "shop_cloth": ("Clothier", "Sailcloth, linen, oilskins. Come in out of the weather.", "A dry man is a cheerful man. Oilskins work wonders.",
                   "Sailcloth, linen, oilskin coats and woollen caps."),
    "shop_cooper": ("Cooper", "Barrels! Water, salt pork, rum. All sound as a bell.", "A leaking cask has sunk more crews than any storm. Mine do not leak.",
                    "Casks and barrels of every size, hoops and bungs."),
    "shop_sailmaker": ("Sailmaker", "Need a patch? A new topsail? A seam stitched while you wait?", "Canvas is only as good as the stitching. Count the stitches.",
                       "Sails, patches, awnings and flags."),
    "shop_fishmonger": ("Fishmonger", "Fresh from the Row this morning. Smell that? That is honest fish.", "The big market is the Row. I only sell what the Row cannot.",
                        "Smoked herring, salt cod and shellfish."),
    "shop_provisioner": ("Provisioner", "Salt pork, dried peas, lime juice. The ship's pantry in one shop.", "Plan the voyage by the pantry. Ask any old hand.",
                         "Salt pork, dried peas, lime juice, cheese."),
    "smithy": ("Smith", "Mind the sparks. What are we mending?", "Nails, hinges, anchor shackles. Every ship is iron held together by wood.",
               "Ironwork, nails, shackles and blades."),
    "carpenter": ("Carpenter", "Planks, pegs and patience. Which do you need?", "A hull is only a very big barrel. Treat her like one.",
                  "Planks, timber, pegs and pitch."),
}

KEY = {
    "tavern": ("Tavernkeeper", "Hargrave Dunn", "Welcome to the Anchor and Crown! Soup, ale, and a seat out of the wind.",
               "Sailors talk. I listen. Ask me what I hear.", "Soup, ale, rum and a rumour or two."),
    "inn": ("Innkeeper", "Phineas Mott", "A bed for the night, Captain? Clean sheets, no fleas, mostly.", "Merchants pay for quiet. Captains pay for a view of the harbour.",
            "Rooms, supper, stabling for nothing, since no one keeps a horse here."),
    "customs": ("Customs clerk", "Clerk Edwin Pratt", "Customs House. Declare your cargo, Captain, and mind the ink.", "Fish pays no duty at Anvil Harbor. Silk and spirits pay plenty.",
                "Duties, permits, harbour fees."),
    "exchange": ("Exchange broker", "Broker Silas Wolfe", "The Exchange! Where a cargo becomes a rumour, and a rumour becomes a price.", "Buy low, sail far, sell high. The sailing is the hard part.",
                 "Cargo brokerage and price news."),
    "counting": ("Treasury clerk", "Master Aldous Crane", "The Counting House. Reales weighed, doubloons assayed.", "A piece of eight is twenty-seven grams of silver. I have weighed them all.",
                 "Coin weighing, assay and exchange."),
    "palace": ("Palace steward", "Steward Hollis Crane", "The Governor receives no one today. But the harbour is open to all honest captains.",
               "The Governor keeps the harbour peace. The harbour keeps the Governor's table.", "Governor's household."),
    "gate": ("Gate guard", "", "Halt. State your business. ... Ah, a captain. Pass.", "The North Road leads to the wild half of the island. Take water.", ""),
    "yard": ("Shipwright", "Master Barnard Quill", "Mind the keel! She's three weeks from the water.", "A good hull takes a year. A bad one takes a week.", "Hulls, repairs and chandlery."),
}
