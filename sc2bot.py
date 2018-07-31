import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import HATCHERY, DRONE, OVERLORD, LARVA

class sc2Bot(sc2.BotAI):
	async def on_step(self, iteration):
		await self.distribute_workers()
		await self.hatch_more_drones()
		await self.hatch_more_overlords()

	async def hatch_more_drones(self):
		if self.can_afford(DRONE) and self.units(LARVA).exists:
			for larva in self.units(LARVA):
				await self.do(larva.train(DRONE))

	async def hatch_more_overlords(self):
		for larva in self.units(LARVA):
			if self.can_afford(OVERLORD) and self.supply_left < 3:
				await self.do(larva.train(OVERLORD))


run_game(maps.get("(2)LostandFoundLE"), [
	Bot(Race.Zerg, sc2Bot()),
	Computer(Race.Terran, Difficulty.Easy)
	], realtime=True)