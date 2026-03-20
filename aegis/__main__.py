"""Allow running AEGIS with: python -m aegis"""

import asyncio

from aegis.main import main

asyncio.run(main())
