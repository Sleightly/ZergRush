import sc2
import random
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *

class sc2Bot(sc2.BotAI):
	async def on_step(self, iteration):
		await self.distribute_workers()
		await self.make_choice()
		await self.expand()
		await self.hatch_more_overlords()
		await self.build_sp()
		await self.construct_queen()
		await self.inject_larva()

	async def make_choice(self):
		game_time = self.state.game_loop * 0.725 * (1/16)
		if game_time <= 90:
			await self.hatch_more_drones()
			return

		choice = random.randrange(0, 4)
		if choice % 2 == 0:
			await self.hatch_more_drones()
			return 
		elif choice % 2 == 1:
			await self.construct_zerglings()
			return

	async def hatch_more_drones(self):
		larvae = self.units(LARVA)
		if larvae.exists: 
			if self.can_afford(DRONE) and self.supply_left > 0:
				await self.do(larvae.random.train(DRONE))
				return

	async def hatch_more_overlords(self):
		larvae = self.units(LARVA)
		if larvae.exists: 
			if self.can_afford(OVERLORD) and not self.already_pending(OVERLORD) and self.supply_left < 3:
				await self.do(larvae.random.train(OVERLORD))
				return

	async def construct_queen(self):
		if self.units(SPAWNINGPOOL).ready.exists:
			if len(self.units(QUEEN)) <  len(self.townhalls) + 2: 
				num_queens = len(self.units(QUEEN))
				num_hatches = len(self.townhalls)
				for i in range(len(self.townhalls)):
					if num_queens > num_hatches + 2:
						return

					if self.townhalls[i].is_ready and self.townhalls[i].noqueue:
						if self.can_afford(QUEEN):
							await self.do(self.townhalls[i].train(QUEEN))
							num_queens = num_queens + 1

	async def inject_larva(self):
		for queen in self.units(QUEEN).idle:
		 	abilities = await self.get_available_abilities(queen)
		 	if AbilityId.EFFECT_INJECTLARVA in abilities:
		 		await self.do(queen(EFFECT_INJECTLARVA, self.townhalls[0]))

	async def expand(self):
		game_time = (self.state.game_loop * 0.725*(1/16) / 60 / 4) + 2#in every 4 minutes
		if (game_time > len(self.townhalls) or (self.minerals > 900)) and self.can_afford(HATCHERY):
			await self.expand_now()

	async def build_sp(self):
		if not self.units(SPAWNINGPOOL).exists and not self.already_pending(SPAWNINGPOOL):
			if self.can_afford(SPAWNINGPOOL):
				await self.build(SPAWNINGPOOL, near=self.townhalls.first)

	async def construct_zerglings(self):
		game_time = self.state.game_loop * 0.725*(1/16)
		if game_time >= 120:
			larvae = self.units(LARVA)
			if larvae.exists: 
				if self.can_afford(ZERGLING) and self.supply_left > 4:
					await self.do(larvae.random.train(ZERGLING))
					return

run_game(maps.get("(2)LostandFoundLE"), [
	Bot(Race.Zerg, sc2Bot()),
	Computer(Race.Terran, Difficulty.Easy)
	], realtime=True)