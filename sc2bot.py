import sc2
import random
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *

class sc2Bot(sc2.BotAI):
	def __init__(self):
		self.first_gas = False
		self.thirty_gas = False
		self.mboost_started = False
		self.extractor_count = 0

	async def on_step(self, iteration):
		await self.distribute_workers()
		await self.make_choice()
		await self.expand()
		await self.get_vespene()
		await self.hatch_more_overlords()
		await self.build_sp()
		await self.construct_queen()
		await self.inject_larva()
		await self.get_zergling_speed()

	def select_target(self):
		if self.known_enemy_structures.exists:
			return random.choice(self.known_enemy_structures).position
		return self.enemy_start_locations[0]

	async def make_choice(self):
		game_time = self.state.game_loop * 0.725 * (1/16)
		if game_time <= 90:
			await self.hatch_more_drones()
			return


		choice = random.randrange(0, 4)
		if len(self.units(DRONE)) >= 75:
			if choice % 2 == 0:
				await self.construct_zerglings()
				return
			else:
				await self.send_zerglings()
				return

		if choice % 2 == 0:
			await self.hatch_more_drones()
			return 
		elif choice == 1:
			await self.construct_zerglings()
			return
		else:
			await self.send_zerglings()
			return

	async def get_vespene(self):
		#build first extractor
		if len(self.units(DRONE)) >= 16 and not self.first_gas:
			if self.can_afford(EXTRACTOR):
				drone = self.workers.random
				target = self.state.vespene_geyser.closest_to(drone.position)
				err = await self.do(drone.build(EXTRACTOR, target))
				if not err:
					self.first_gas = True
					self.extractor_count = self.extractor_count + 1

		if len(self.units(DRONE)) >= 30 and not self.thirty_gas:
			if self.can_afford(EXTRACTOR):
				drone = self.workers.random
				target = self.state.vespene_geyser.closest_to(drone.position)
				err = await self.do(drone.build(EXTRACTOR, target))
				if not err:
					self.extractor_count = self.extractor_count + 1
					if self.extractor_count >= 4:
						self.thirty_gas = True

		if len(self.units(DRONE)) >= 50:
			if self.can_afford(EXTRACTOR) and self.extractor_count * 2 < len(self.townhalls):
				drone = self.workers.random
				target = self.state.vespene_geyser.closest_to(drone.position)
				err = await self.do(drone.build(EXTRACTOR, target))
				if not err:
					self.extractor_count = self.extractor_count + 1

	async def hatch_more_drones(self):
		larvae = self.units(LARVA)
		if larvae.exists: 
			if self.can_afford(DRONE) and self.supply_left > 0 and len(self.units(DRONE)) <= 75:
				await self.do(larvae.random.train(DRONE))

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

	async def get_zergling_speed(self):
		 if self.vespene >= 100:
		 	sp = self.units(SPAWNINGPOOL).ready
		 	if sp.exists and self.minerals >= 100 and not self.mboost_started:
		 		err = await self.do(sp.first(RESEARCH_ZERGLINGMETABOLICBOOST))
		 		if not err:
		 			self.mboost_started = True

	async def send_zerglings(self):
		if len(self.units(ZERGLING)) > 40:
			for unit in self.units(ZERGLING):
				await self.do(unit.attack(self.select_target()))

run_game(maps.get("(2)LostandFoundLE"), [
	Bot(Race.Zerg, sc2Bot()),
	Computer(Race.Protoss, Difficulty.Medium)
	], realtime=True)