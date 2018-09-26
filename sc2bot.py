import sc2
import random
from sc2 import run_game, maps, Race, Difficulty
from sc2.helpers.control_group import *
from sc2.player import Bot, Computer
from sc2.constants import *
import cv2
import numpy as np

class sc2Bot(sc2.BotAI):
	def __init__(self):
		self.first_gas = False
		self.thirty_gas = False
		self.mboost_started = False
		self.chooks_started = False
		self.extractor_count = 0
		self.building_lair = False

	async def on_step(self, iteration):
		await self.intel()
		await self.distribute_workers()
		await self.make_choice()
		await self.expand()
		await self.get_vespene()
		await self.hatch_more_overlords()
		await self.build_sp()
		await self.build_bn()
		await self.construct_queen()
		await self.inject_larva()
		await self.get_zergling_speed()
		await self.get_baneling_speed()
		self.print_score()


	def select_target(self):
		if self.known_enemy_structures.exists:
			return random.choice(self.known_enemy_structures).position
		return self.enemy_start_locations[0]

	def print_score(self):
		sd = self.state.score
		score_values = []
		score_values.append(sd.collected_minerals)
		score_values.append(sd.collected_vespene)
		score_values.append(sd.total_value_units)
		score_values.append(sd.total_value_structures)
		score_values.append(sd.killed_value_units)
		score_values.append(sd.killed_value_structures)
		print(score_values)

	async def make_choice(self):
		game_time = self.state.game_loop * 0.725 * (1/16)
		if game_time <= 90:
			await self.hatch_more_drones()
			return

		if game_time >= 210 and not self.building_lair:
			await self.build_lair()
			return

		if game_time >= 270:
			await self.build_hd()

		choice = random.randrange(0, 6)
		if len(self.units(DRONE)) >= 75:
			if choice % 2 == 0:
				await self.construct_zerglings()
				return
			else:
				await self.send_units()
				return

		if choice == 0:
			await self.hatch_more_drones()
			return 
		elif choice == 1:
			await self.construct_zerglings()
			return
		elif choice == 2:
			await self.construct_banelings()
			return
		elif choice == 4:
			await self.send_units()
			return
		else:
			await self.construct_hydralisks()
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
			if len(self.units(QUEEN)) <  len(self.townhalls): 
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
		if len(self.units(QUEEN)) > 0:
			queen = self.units(QUEEN).random
			if queen.energy >= 25:
				closest_base = self.townhalls.closest_to(queen.position)
				if closest_base.has_buff(QUEENSPAWNLARVATIMER):
					#find next closest base
					set_base = False
					for base in self.townhalls:
						if not base.has_buff(QUEENSPAWNLARVATIMER):
							closest_base = base
							set_base = True
							break	

					if set_base:
						await self.do(queen(EFFECT_INJECTLARVA, closest_base))
						return
					else:
						return
				else:
					await self.do(queen(EFFECT_INJECTLARVA, closest_base))
					return
				return
		

	async def expand(self):
		game_time = (self.state.game_loop * 0.725*(1/16) / 60 / 4) + 2 #in every 4 minutes
		if (game_time > len(self.townhalls) or (self.minerals > 900)) and self.can_afford(HATCHERY):
			await self.expand_now()

	async def get_zergling_speed(self):
		if self.vespene >= 100 and self.minerals >= 100:
		 	sp = self.units(SPAWNINGPOOL).ready
		 	if sp.exists and self.minerals >= 100 and not self.mboost_started:
		 		err = await self.do(sp.first(RESEARCH_ZERGLINGMETABOLICBOOST))
		 		if not err:
		 			self.mboost_started = True

	async def get_baneling_speed(self):
		if self.vespene >= 150:
		 	bn = self.units(BANELINGNEST).ready
		 	if bn.exists and self.minerals >= 150 and not self.chooks_started:
		 		err = await self.do(bn.first(RESEARCH_CENTRIFUGALHOOKS))
		 		if not err:
		 			self.chooks_started = True

	async def build_sp(self):
		size = len(self.townhalls)-1
		if not self.units(SPAWNINGPOOL).exists and not self.already_pending(SPAWNINGPOOL):
			if self.can_afford(SPAWNINGPOOL):
				await self.build(SPAWNINGPOOL, near=self.townhalls[size])

	async def build_bn(self):
		size = len(self.townhalls)-1
		if self.units(SPAWNINGPOOL).ready.exists:
			if not self.units(BANELINGNEST).exists:
				if self.can_afford(BANELINGNEST):
					await self.build(BANELINGNEST, near=self.townhalls[size])

	async def build_hd(self):
		size = len(self.townhalls)-1
		if self.units(LAIR).ready.exists:
			if not self.units(HYDRALISKDEN).exists:
				if self.can_afford(HYDRALISKDEN):
					await self.build(HYDRALISKDEN, near=self.townhalls[size])

	async def build_lair(self):
		size = len(self.townhalls)-1
		if self.units(SPAWNINGPOOL).ready.exists:
			if not self.units(LAIR).exists and self.townhalls[size].noqueue and not self.building_lair:
				if self.can_afford(LAIR):
					err = await self.do(self.townhalls[size].build(LAIR))
					if not err:
						self.building_lair = True


	async def construct_zerglings(self):
		game_time = self.state.game_loop * 0.725*(1/16)
		if game_time >= 120:
			larvae = self.units(LARVA)
			if larvae.exists: 
				if self.can_afford(ZERGLING) and self.supply_left > 4:
					await self.do(larvae.random.train(ZERGLING))
					return

	async def construct_banelings(self):
		game_time = self.state.game_loop * 0.725*(1/16)
		if game_time >= 120:
			lings = self.units(ZERGLING)
			if lings.exists and lings.amount > self.units(BANELING).amount*2 and self.supply_left > 4:
				if self.can_afford(BANELING):
					await self.do(lings.random.train(BANELING))
			else:
				await self.construct_zerglings()
				return

	async def construct_hydralisks(self):
		game_time = self.state.game_loop * 0.725*(1/16)
		if game_time >= 300:
			larvae = self.units(LARVA)
			if larvae.exists: 
				if self.can_afford(HYDRALISK) and self.supply_left > 4:
					await self.do(larvae.random.train(HYDRALISK))
					return

	async def send_units(self):
		lings = self.units(ZERGLING)
		banes = self.units(BANELING)
		hydras = self.units(HYDRALISK)
		if (len(lings) > 40 or len(banes) > 10) or len(hydras) > 10:
			for unit in lings:
				await self.do(unit.attack(self.select_target()))
			for unit in banes:
				await self.do(unit.attack(self.select_target()))
			for unit in hydras:
				await self.do(unit.attack(self.select_target()))


	async def intel(self):
		size_chart = {
			HATCHERY: [15, (255, 255, 255)],
			OVERLORD: [3, (20, 235, 0)],
			DRONE: [1, (55, 200, 0)],
			EXTRACTOR: [2, (55, 200, 0)],
			SPAWNINGPOOL: [5, (200, 100, 0)],
			BANELINGNEST: [5, (150, 150, 0)],
			HYDRALISKDEN: [5, (255, 0, 0)],
			ZERGLING: [3, (200, 100, 0)],
			BANELING: [3, (150, 150, 0)],
			HYDRALISK: [3, (255, 0, 0)],
		}


		game_data = np.zeros((self.game_info.map_size[1], self.game_info.map_size[0], 3), np.uint8)
		
		for unit_type in size_chart:
			for unit in self.units(unit_type).ready:
				pos = unit.position
				cv2.circle(game_data, (int(pos[0]), int(pos[1])), size_chart[unit_type][0], size_chart[unit_type][1], 1)

		flipped = cv2.flip(game_data, 0)
		resized = cv2.resize(flipped, dsize=None, fx=2, fy=2)

		cv2.imshow('Intel', resized)
		cv2.waitKey(1)


run_game(maps.get("(2)LostandFoundLE"), [
	Bot(Race.Zerg, sc2Bot()),
	Computer(Race.Protoss, Difficulty.Hard)
	], realtime=True)