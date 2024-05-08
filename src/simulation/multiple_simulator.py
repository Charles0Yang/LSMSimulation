from src.data_scripts.basic_generation import generate_data
from src.simulation.metrics import Metrics
from src.simulation import settings
from src.simulation.day_simulator import simulate_day_transactions
from src.simulation.setup import generate_banks
import numpy as np
import matplotlib.pyplot as plt

from src.utils.csvutils import write_to_csv


# Goal of this class is to take in configs and number of days to run simulator then return relevant metrics
class MultipleSimulator:

    def __init__(self):
        self.data_generation_config = settings.data_generation_config
        self.day_config = settings.day_config
        self.csv_settings = settings.csv_settings
        self.num_passes = settings.num_passes
        self.banks = generate_banks(settings.day_config.bank_types,
                                    settings.day_config.starting_balance,
                                    settings.csv_settings.input_file_name)
        self.all_normal_banks = generate_banks(settings.day_config_benchmark.bank_types,
                                               settings.day_config.starting_balance,
                                               settings.csv_settings.input_file_name)
        self.metrics = []

    def one_pass_full_run(self):
        if settings.generate_new_data:
            generate_data(settings.data_generation_config)
        metrics = Metrics()
        banks, collected_metrics = simulate_day_transactions(self.banks, metrics)
        self.metrics.append(collected_metrics)
        for bank in banks:
            print(f"{bank}: {banks[bank].min_balance}")
            if bank == 5:
                print(banks[bank].delay_percentage/1000)

        return banks

    def test_liquidity_saving_against_payment_amount_ratio(self):
        payment_amount_ratios = []
        starting_ratio = 0.01
        while starting_ratio <= 1:
            payment_amount_ratios.append(starting_ratio)
            starting_ratio += 0.01
        for ratio in payment_amount_ratios:
            print(ratio)
            settings.data_generation_config.min_transaction_amount = int(settings.day_config.starting_balance * ratio)
            settings.data_generation_config.max_transaction_amount = int(settings.day_config.starting_balance * ratio)
            generate_data(settings.data_generation_config)
            self.banks = generate_banks(settings.day_config.bank_types,
                                        settings.day_config.starting_balance,
                                        settings.csv_settings.input_file_name)
            metrics = Metrics()
            banks, collected_metrics = simulate_day_transactions(self.banks, metrics)
            self.metrics.append(collected_metrics)
        saved_ratios = []
        for metric in self.metrics:
            saved_ratios.append(metric.liquidity_saved_ratio)
        print(saved_ratios)

    def test_liquidity_saving_against_non_priority_percentage(self):
        non_priority_percentages = [0.1, 0.5, 0.9]
        payment_sizes = [0.01, 0.1, 0.2]
        transaction_nums = []
        num = 35
        while num <= 50000:
            transaction_nums.append(num)
            if num < 100:
                num += 35
            elif num < 1000:
                num += 105
            elif num < 10000:
                num += 350
            elif num <= 50000:
                num += 1050
        for size in payment_sizes:
            for num in transaction_nums:
                print(num)
                settings.data_generation_config.min_transaction_amount = settings.day_config.starting_balance * size
                settings.data_generation_config.max_transaction_amount = settings.day_config.starting_balance * size
                settings.data_generation_config.num_transactions = num
                generate_data(settings.data_generation_config)
                self.banks = generate_banks(settings.day_config.bank_types,
                                            settings.day_config.starting_balance,
                                            settings.csv_settings.input_file_name)
                metrics = Metrics()
                banks, collected_metrics = simulate_day_transactions(self.banks, metrics)
                self.metrics.append(collected_metrics)
            saved_ratios = []
            for metric in self.metrics:
                saved_ratios.append(metric.liquidity_saved_ratio)
            print(f'{size}: {saved_ratios}')


    def multiple_run(self):
        ratios = [0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.15, 0.2]
        for i in range(len(ratios)):
            print(i)
            settings.data_generation_config.min_transaction_amount = settings.day_config.starting_balance * ratios[i] /2
            settings.data_generation_config.min_transaction_amount = settings.day_config.starting_balance * ratios[i] *2
            generate_data(data_generation_config=settings.data_generation_config)
            self.banks = generate_banks(settings.day_config.bank_types,
                                        settings.day_config.starting_balance,
                                        settings.csv_settings.input_file_name)
            metrics = Metrics()
            banks, metrics = simulate_day_transactions(self.banks, metrics)
            self.metrics.append(metrics)
        delays = []
        for metric in self.metrics:
            delays.append(metric.calculate_average_delay_per_transaction())
        print(delays)

    def compare_delay_behaviour_original(self):
        delay_nums = []
        non_delay_nums = []
        delay_amounts = [300, 600, 900, 1200, 1500, 1800, 2100, 2400, 2700, 3000]
        for delay_amount in delay_amounts:
            if settings.generate_new_data:
                generate_data(settings.data_generation_config)
                settings.delay_amount = delay_amount
                self.banks = generate_banks(settings.day_config.bank_types,
                                            settings.day_config.starting_balance,
                                            settings.csv_settings.input_file_name)
                self.all_normal_banks = generate_banks(settings.day_config_benchmark.bank_types,
                                                       settings.day_config.starting_balance,
                                                       settings.csv_settings.input_file_name)

            metrics = Metrics()
            normal_banks, collected_metrics = simulate_day_transactions(self.all_normal_banks, metrics)
            metrics = Metrics()
            original_banks, collected_metrics = simulate_day_transactions(self.banks, metrics)

            delay_min_balances = [original_banks[bank].min_balance for bank in original_banks]
            no_delay_min_balances = [normal_banks[bank].min_balance for bank in normal_banks]
            bank_balances = list(zip(delay_min_balances, no_delay_min_balances))

            average_non_delay_change = []
            average_delay_change = 0
            for bank in original_banks:
                difference_from_delaying = (bank_balances[bank][0] - bank_balances[bank][1]) / bank_balances[bank][1]
                if bank == 37:
                    average_delay_change = difference_from_delaying
                else:
                    average_non_delay_change.append(difference_from_delaying)
            mean_change_non_delay = np.average(np.array(average_non_delay_change))
            delay_nums.append(average_delay_change)
            non_delay_nums.append(mean_change_non_delay)

        print()

    def compare_delay_behaviour_liquidity_savings(self):
        delay_nums = []
        non_delay_nums = []
        delay_amounts = [300, 600, 900, 1200, 1500, 1800, 2100, 2400, 2700, 3000]
        for i in range(20):
            print(i)
            if settings.generate_new_data:
                generate_data(settings.data_generation_config)
                settings.delay_amount = 3600
                self.banks = generate_banks(settings.day_config.bank_types,
                                            settings.day_config.starting_balance,
                                            settings.csv_settings.input_file_name)
                self.all_normal_banks = generate_banks(settings.day_config_benchmark.bank_types,
                                                       settings.day_config.starting_balance,
                                                       settings.csv_settings.input_file_name)

            metrics = Metrics()
            normal_banks, collected_metrics = simulate_day_transactions(self.all_normal_banks, metrics)
            metrics = Metrics()
            original_banks, collected_metrics = simulate_day_transactions(self.banks, metrics)

            delay_min_balances = [original_banks[bank].min_balance for bank in original_banks]
            no_delay_min_balances = [normal_banks[bank].min_balance for bank in normal_banks]
            bank_balances = list(zip(delay_min_balances, no_delay_min_balances))

            for bank in original_banks:
                if bank_balances[bank][1] != 0:
                    difference_from_delaying = (bank_balances[bank][0] - bank_balances[bank][1])
                    if bank >= 19:
                        delay_nums.append(difference_from_delaying)
                    else:
                        non_delay_nums.append(difference_from_delaying)

        print(delay_nums)
        print(non_delay_nums)

        """
        for i in range(3, len(original_banks)):
            print(f"Bank {original_banks[i].name} delayed {original_banks[i].calculate_percentage_transactions_delayed() * 100:.2f}% of transactions")

        for i in range(3, len(original_banks)):
            print(f"Bank {original_banks[i].name} delayed {original_banks[i].calculate_average_delay_per_transaction():.2f} minutes per transaction on average")

        delay_min_balances = [original_banks[bank].min_balance for bank in original_banks]
        no_delay_min_balances = [normal_banks[bank].min_balance for bank in normal_banks]
        bank_balances = list(zip(delay_min_balances, no_delay_min_balances))

        print(no_delay_min_balances)
        print(delay_min_balances)

        for bank in original_banks:
            difference_from_delaying = (bank_balances[bank][0] - bank_balances[bank][1]) / bank_balances[bank][1]
            if difference_from_delaying >= 0:
                print(f"Bank {original_banks[bank].name} benefited {difference_from_delaying * 100:.2f}% in min liquidity from banks delaying")
            else:
                print(f"Bank {original_banks[bank].name} lost {difference_from_delaying * 100:.2f}% in min liquidity from banks delaying")
        """

    def compare_DPs_on_savings_and_liquidity(self):
        non_delay_nums = []
        non_delay_delays = []
        rule_delay_nums = []
        rule_delay_delays = []
        rl_delay_nums = []
        rl_delay_delays = []
        conservative_delay_nums = []
        conservative_delay_delays = []
        for i in range(self.num_passes):
            print(i)
            if settings.generate_new_data:
                generate_data(settings.data_generation_config)
                settings.delay_amount = 1800
                self.banks = generate_banks(settings.day_config.bank_types,
                                            settings.day_config.starting_balance,
                                            settings.csv_settings.input_file_name)
                self.all_normal_banks = generate_banks(settings.day_config_benchmark.bank_types,
                                                       settings.day_config.starting_balance,
                                                       settings.csv_settings.input_file_name)

            metrics = Metrics()
            normal_banks, collected_metrics = simulate_day_transactions(self.all_normal_banks, metrics)

            metrics = Metrics()
            original_banks, collected_metrics = simulate_day_transactions(self.banks, metrics)

            for bank in original_banks:
                dp = original_banks[bank]
                if bank <= 4:
                    non_delay_delays.append(dp.calculate_average_delay_per_transaction())
                elif bank <= 9:
                    rule_delay_delays.append(dp.calculate_average_delay_per_transaction())
                elif bank <= 14:
                    print(dp.delay_percentage)
                    rl_delay_delays.append(dp.calculate_average_delay_per_transaction())
                elif bank <= 19:
                    conservative_delay_delays.append(dp.calculate_average_delay_per_transaction())

            delay_min_balances = [original_banks[bank].min_balance for bank in original_banks]
            no_delay_min_balances = [normal_banks[bank].min_balance for bank in normal_banks]
            bank_balances = list(zip(delay_min_balances, no_delay_min_balances))

            for bank in original_banks:
                difference_from_delaying = (bank_balances[bank][0] - bank_balances[bank][1])
                if bank <= 4:
                    non_delay_nums.append(difference_from_delaying)
                elif bank <= 9:
                    rule_delay_nums.append(difference_from_delaying)
                elif bank <= 14:
                    rl_delay_nums.append(difference_from_delaying)
                elif bank <= 19:
                    conservative_delay_nums.append(difference_from_delaying)

        print(non_delay_nums)
        print(rule_delay_nums)
        print(rl_delay_nums)
        print(conservative_delay_nums)
        print(non_delay_delays)
        print(rule_delay_delays)
        print(rl_delay_delays)
        print(conservative_delay_delays)

    def compare_characteristic_on_datasets(self):
        characteristic_delay_liquidities = []
        characteristic_delay_delays = []
        characteristic_non_delay_liquidities = []
        characteristic_non_delay_delays = []
        for i in range(self.num_passes):
            print(i)
            if settings.generate_new_data:
                generate_data(settings.data_generation_config)
                self.banks = generate_banks(settings.day_config.bank_types,
                                            settings.day_config.starting_balance,
                                            settings.csv_settings.input_file_name)
                self.all_normal_banks = generate_banks(settings.day_config_benchmark.bank_types,
                                                       settings.day_config.starting_balance,
                                                       settings.csv_settings.input_file_name)

            metrics = Metrics()
            normal_banks, collected_metrics = simulate_day_transactions(self.all_normal_banks, metrics)
            metrics = Metrics()
            original_banks, collected_metrics = simulate_day_transactions(self.banks, metrics)

            delay_min_balances = [original_banks[bank].min_balance for bank in original_banks]
            no_delay_min_balances = [normal_banks[bank].min_balance for bank in normal_banks]
            bank_balances = list(zip(delay_min_balances, no_delay_min_balances))

            for bank in original_banks:
                difference_from_delaying = (bank_balances[bank][0] - bank_balances[bank][1])
                if bank <= 19:
                    characteristic_non_delay_liquidities.append(difference_from_delaying)
                    characteristic_non_delay_delays.append(original_banks[bank].calculate_average_delay_per_transaction())
                else:
                    characteristic_delay_liquidities.append(difference_from_delaying)
                    characteristic_delay_delays.append(original_banks[bank].calculate_average_delay_per_transaction())

        print(characteristic_delay_liquidities)
        print(characteristic_non_delay_liquidities)

        print(characteristic_delay_delays)
        print(characteristic_non_delay_delays)

    def calc_average_min_balance(self, banks):
        total_min_balance = 0
        for bank in banks:
            total_min_balance += banks[bank].min_balance

        return total_min_balance / (len(banks.keys()))

    def calc_average_settlement_delay(self, banks):
        total_settlement_delay = 0
        for bank in banks:
            total_settlement_delay += banks[bank].cum_settlement_delay

        return total_settlement_delay / (len(banks.keys()) * 360)  # Calculate in hours

    def collect_metrics(self, banks):
        metrics = [
            self.calc_average_min_balance(banks),
            self.calc_average_settlement_delay(banks)
        ]
        return metrics

    def plot(self):
        liquidity_savings = [0.23224513172966782, 0.2381906670483825, 0.24534250501576382, 0.22874320068708845, 0.23779437105112006, 0.263670197537933, 0.26802642918701525, 0.3084031186832226, 0.2883949191685912, 0.31987216734456714, 0.3163383545770568, 0.35268505079825835, 0.4224817518248175, 0.39959016393442626, 0.44123651210265386, 0.44989654153118536, 0.46527369040612127, 0.456379821958457, 0.42394822006472493, 0.4525721082366934, 0.5091988130563798, 0.5403580862929264, 0.5243501643262624, 0.49792408066429417, 0.5293040293040293, 0.6602813528883568, 0.5793368857312019, 0.5970193740685544, 0.5727923627684964, 0.5476261570618095, 0.5885850178359097, 0.5926814637072585, 0.587221396731055, 0.6747499242194605, 0.678003120124805, 0.667178856791641, 0.6913464542330522, 0.6971875, 0.7045033929673041, 0.6730061349693252, 0.6961030798240101, 0.6536953242835596, 0.6943270971635486, 0.678967896789679, 0.6565958719712833, 0.6930426993132278, 0.6717049576783555, 0.7444041137326074, 0.699781999377141, 0.7484472049689441, 0.8112791430371771, 0.763166095356809, 0.813296054675365, 0.7822006472491909, 0.7948797038864899, 0.8263042799125273, 0.75177523927138, 0.7994995308101345, 0.7774992165465371, 0.7695881077733044, 0.77299473521214, 0.8005181347150259, 0.8258928571428571, 0.8228900255754475, 0.8220234423195558, 0.835091083413231, 0.8024306637581802, 0.8074712643678161, 0.8124203821656051, 0.8199316982303633, 0.7955944282474895, 0.8127795527156549, 0.7957526545908807, 0.8524133663366337, 0.7822936357908002, 0.8263207845618475, 0.8011015911872705, 0.8061842524705132, 0.7894248608534323, 0.7847394540942928, 0.7994251038007026, 0.8145187080268628, 0.8069118579581483, 0.79361636194608, 0.8162128712871287, 0.8437197287697772, 0.7520299812617114, 0.7876160990712074, 0.7946138870863076, 0.7817670933499844, 0.7706755528627689, 0.8102143757881463, 0.8176301501117854, 0.8065635847270433, 0.7944988934555801, 0.816798732171157, 0.821831869510665, 0.7908496732026143, 0.7654472794343683]
        priority_payment_liquidity_savings = [0.0, 0.0014371785202823514, 0.004513050258160697, 0.004582452995283522, 0.0082973281431512,0.009349007611073053, 0.01648429425629236, 0.020309824683700493, 0.01985910313893658, 0.032107275751496134,0.032291144648270986, 0.04232899143836055, 0.04736126653713862, 0.04929445450226622, 0.05850500496840439,0.05786146830208382, 0.06401484943838884, 0.07358336905272182, 0.07928927991476858, 0.08452309868413128,0.10248322785083364, 0.10243502945412042, 0.11231700722146581, 0.10971970786841688, 0.11308838611105297,0.12206509745911706, 0.13603992651925634, 0.1390487438545103, 0.15259702937877512, 0.14949481302105797,0.15541537396710522, 0.1726184761813332, 0.18444177533047706, 0.17930072151381768, 0.1980751475862045,0.208476246187201, 0.20780060342416642, 0.22361967179915135, 0.22911663276422883, 0.2389065525111783,0.2453401905935568, 0.259885771952795, 0.2554321502240937, 0.2683729206322933, 0.28184383932912427,0.2810050983248361, 0.2972483547163063, 0.3031322477980397, 0.31718995721653376, 0.3022389483690561,0.3261050276311027, 0.33288569630417325, 0.34671894264182956, 0.3552905523198054, 0.3659923290318962,0.37453314224602635, 0.3780615030023655, 0.3748074786702678, 0.3872365595768177, 0.3993752193448035,0.3964336692302776, 0.40893844627455067, 0.41991442389876793, 0.4286044976087181, 0.4384482270833008,0.45519305100973956, 0.4491790706651776, 0.47030438010393466, 0.479367936468247, 0.49070098772613985,0.4920344813436919, 0.4952006984548318, 0.49726564577247223, 0.5008269399807133, 0.5204515046887485,0.5430621348048577, 0.5428166947034676, 0.5492061167979398, 0.5279752409126156, 0.5542530989830614,0.561205418183157, 0.5901442483834233, 0.5827890748143626, 0.5916155399993333, 0.6129834138076214,0.6092072005689169, 0.6197898726917641, 0.6161395257960244, 0.6223597134572745, 0.6203376762497399,0.6389166693827698, 0.6456880838995195, 0.6645809559222645, 0.675807534578232, 0.6756145536130477,0.6744480827237007, 0.6904970181657105, 0.7120016192782939, 0.7155515355347194, 0.70412322623212]
        priority_payment_liquidity_savings_1 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0011321822813472968, 0.0015385355065147363, 0.0, 0.0, 0.0006219679064560268, 0.00162821503477205, 0.0008925914906277894, 0.0, 0.0008436326823301135, 0.002284686523995285, 0.001575069503905961, 0.002774145339062208, 0.0025688441874670525, 0.002358978286677134, 0.003047407971742217, 0.004512892130240256, 0.004594870562796565, 0.004205487266097733, 0.003521348503295688, 0.0052102679920162055, 0.0042366963080217885, 0.004676972917167294, 0.007129528943348806, 0.007379465380856823, 0.006475574486390155, 0.008933695457486356, 0.006493942402476036, 0.007960104873368111, 0.011847802062070131, 0.00876792943175571, 0.009525617613201464, 0.00860021914718611, 0.011942193171241663, 0.012854658180753814, 0.014786818298603129, 0.01904781691823442, 0.017883289227143658, 0.018996250598451826, 0.022184450569170656, 0.017262035470245553, 0.017508144554114022, 0.020142549504412074, 0.02388694569396662, 0.02654222268830454, 0.024038081619597734, 0.02644452704404024, 0.027095914946382235, 0.030976953501822207, 0.029222741947239575, 0.028831115634774838, 0.031965596526948255, 0.032036697318644614, 0.03198614372616119, 0.0279597081744321, 0.03175464772971204, 0.03572249982537408, 0.03277970874938993, 0.03214963759795852, 0.02512509955369889, 0.03004726014703157, 0.0341128168511246, 0.027843434425659324, 0.03419951904943526, 0.026893142164080907, 0.031066313648119563, 0.03300242480091965, 0.03014341792491144, 0.03716518481678652, 0.03186867515739]
        priority_payment_liquidity_savings_2 = [0.0, 0.0, 0.0, 0.002810172825628776, 0.011401557285873193, 0.00459738088604068, 0.0058341130497000385, 0.010522360015031942, 0.01125370948471885, 0.015120967741935484, 0.020745440126883424, 0.02304906157392163, 0.02480872266349782, 0.028390474581996283, 0.03404689960420479, 0.040089522668069026, 0.05602217280880168, 0.052503451106219456, 0.05116138357591852, 0.05838632935798361, 0.067010381890152, 0.08000574453779319, 0.0750193963015682, 0.08944754492857508, 0.09686753384656226, 0.09750073157787709, 0.10724365004703669, 0.1087393056319572, 0.12129585152374353, 0.12640450576389312, 0.12632046466572477, 0.14141578519121237, 0.13216513948924988, 0.14360541100191795, 0.15562168380138366, 0.1488982287222982, 0.16094773722273162, 0.1483746407518205, 0.1596387880020662, 0.17559753041139434, 0.1912348002641284, 0.20595879238923212, 0.23311875407104002, 0.23345097420782737, 0.2386209039094759, 0.23879700270935122, 0.2589793068156377, 0.2652972517208545, 0.27176452784923827, 0.2707236531004697, 0.28742483056342655, 0.2836355942449522, 0.29478460164652615, 0.30340545798894203, 0.30058193865360555, 0.29758981119149686, 0.31937225250219, 0.3099655113664256, 0.3131367508084313, 0.31929678543231976, 0.3185569595219765, 0.3207474602114064, 0.3306012842965558, 0.34554710593052135, 0.34300841275533045, 0.3314887373700481, 0.35401397907325277, 0.34897304140601726, 0.3588808892600984, 0.3115507838293918, 0.3595487068836671, 0.35766769867219145, 0.3462944974001444, 0.35390354201049185, 0.3470276200497]
        priority_payment_liquidity_savings_3 = [0.0, 0.0, 0.005577244841048522, 0.006886657101865136, 0.019459962756052142, 0.016725476358503882, 0.03272850602001017, 0.03476567932137394, 0.04106930693069307, 0.05524425040393276, 0.04453749524172059, 0.05331792670848465, 0.0797432362571084, 0.09214851086664878, 0.11223510821411439, 0.1300014532067429, 0.13649610373154816, 0.15311960681323628, 0.1788268594101443, 0.19605012998098786, 0.1998820503346644, 0.22584507871697224, 0.2581866569890522, 0.2428000745842774, 0.24924831740800582, 0.2710968575974543, 0.30094810167719327, 0.293020422500767, 0.3133698574199476, 0.3393537777309716, 0.3398155479994411, 0.3665723609364709, 0.34299639754185207, 0.3430759886624376, 0.3711271840715156, 0.41829836533075315, 0.39012528301886795, 0.38921198577005084, 0.4486027903767844, 0.43118055055559557, 0.43878787332843894, 0.4668739248481834, 0.4911884232272582, 0.5080193672539169, 0.509790009902304, 0.5499022922798739, 0.5475896488041497, 0.5446321649816918, 0.5894802237057134, 0.5967662792744263, 0.5843527360874207, 0.599391026562066, 0.6108577239224796, 0.6005476374671046, 0.6220585817579685, 0.6269009814585806, 0.6495302827820584, 0.6402115197215668, 0.6427119821080258, 0.6588048680184924, 0.6536378153277739, 0.6646766008942161, 0.6652189117129423, 0.6687367761932594, 0.6783669951160464, 0.6878681873944783, 0.680412014819238, 0.6851660126892427, 0.7107698556013953, 0.7084829960603573, 0.6958758032924388, 0.7144967468781398, 0.690506673607723, 0.7153992006726729, 0.71602647996067]

        payment_size_1 = [0.0, 0.0, 0.0, 0.0, 0.006349206349206349, 0.007142857142857143, 0.0038095238095238095, 0.0047694753577106515, 0.014986376021798364, 0.009523809523809525, 0.013785790031813362, 0.020972354623450904, 0.016428571428571428, 0.02177650429799427, 0.028135431568907965, 0.03761242845461979, 0.03716940671908506, 0.045454545454545456, 0.04286939125464419, 0.048621944877795115, 0.050976655550262026, 0.05763308402991641, 0.060432829726418946, 0.06425166825548141, 0.061997498659996424, 0.06932525660440855, 0.06832989035436199, 0.07494356659142212, 0.07742857142857143, 0.08455882352941177, 0.08216328653146125, 0.0893611732537907, 0.0857551214864221, 0.093560562735903, 0.09925176056338028, 0.1008785857944321, 0.10367722165474974, 0.11137417381868403, 0.11100196463654224, 0.12140522875816993, 0.12832091518025138, 0.14262798158739015, 0.13376665583360417, 0.14988133633542264, 0.14879624864184823, 0.15456017269293038, 0.15997548268464604, 0.16156231827873618, 0.16758926100193744, 0.17216503914841208, 0.1736368226186469, 0.18532989607669378, 0.18738648220427406, 0.1890576830219515, 0.19164223922213483, 0.19329728240278304, 0.19764619834435984, 0.19899762256634326, 0.20501740860482467, 0.20195665261890428, 0.2106568618868365, 0.20973814578910122, 0.21315261320210047, 0.21535050224406924, 0.21893521888322762, 0.2185435492444377, 0.22532120046361373, 0.22725087727731577, 0.223657073216462, 0.2254181826502826, 0.23322755106601709, 0.22957011549461825, 0.23299189073836962, 0.23752086811352255, 0.235219611848825]
        payment_size_2 = [0.0, 0.0, 0.0, 0.0, 0.006369426751592357, 0.004761904761904762, 0.009578544061302681, 0.011128775834658187, 0.008174386920980926, 0.02038369304556355, 0.02872340425531915, 0.03358925143953935, 0.046242774566473986, 0.08647707486941382, 0.09597673291323315, 0.07650727650727651, 0.10584752035529238, 0.1166883963494133, 0.12421618393550314, 0.17632586112629853, 0.15874177029992684, 0.1785470280118424, 0.1853956228956229, 0.17609561752988048, 0.20650767239785542, 0.20736022646850671, 0.20592149035262808, 0.2047872340425532, 0.21039309112567003, 0.19795512638454985, 0.23223593964334704, 0.22976298406942106, 0.24085213032581454, 0.23211020358405463, 0.26149061168068194, 0.25426545535120765, 0.23587118788654296, 0.25176967776016906, 0.25306964101602775, 0.298617669786211, 0.28672040065732846, 0.2878009395184968, 0.29321678321678324, 0.29782034346103037, 0.31202846101944426, 0.3025441855229089, 0.3179467844446838, 0.3173355399255275, 0.33595511006666345, 0.33874965574221977, 0.32855657520003617, 0.31800898721050813, 0.32301245015867847, 0.3391796767470211, 0.3311192548480684, 0.3397680563711098, 0.3572169582958711, 0.33613707165109036, 0.35655804547085496, 0.34870362232406305, 0.3456235573023894, 0.3580490724117295, 0.32843695665207745, 0.35886540788473986, 0.3468298544164082, 0.3609903156097431, 0.3481508856215189, 0.3595409257157271, 0.3550649478935151, 0.3678379157854259, 0.36359366928098436, 0.3570733515592419, 0.37225095570047223, 0.3583913005195034, 0.367917117805659]
        payment_size_3 = [0.0, 0.0, 0.0, 0.004807692307692308, 0.00964630225080386, 0.02926829268292683, 0.058823529411764705, 0.06633499170812604, 0.0792507204610951, 0.10039113428943937, 0.0992108229988726, 0.1111111111111111, 0.13266871165644173, 0.18015824710894704, 0.19621251972645976, 0.19399538106235567, 0.2009400705052879, 0.2181881051175657, 0.23384809328710998, 0.22932330827067668, 0.24811422413793102, 0.26948448570730515, 0.25210850239343513, 0.2761559769870019, 0.2835608066816052, 0.2906781244162152, 0.23710355368742836, 0.28853820598006646, 0.3007818733046115, 0.31125827814569534, 0.2908739595719382, 0.3118049615055603, 0.2981862479696806, 0.29982023626091425, 0.31243070099790565, 0.31640669475122396, 0.30180695333943275, 0.2874582517563054, 0.31793288857910984, 0.3186042274052478, 0.33968201391189135, 0.32122013851062176, 0.34565448740688187, 0.3347186265158741, 0.3449262461851475, 0.36008325624421833, 0.34075773686272315, 0.3667164409659647, 0.36270389272490744, 0.3605993497620506, 0.3583863330393204, 0.36376318772342836, 0.3655056133569108, 0.36525514878699755, 0.36361880480550085, 0.3661904761904762, 0.3722981276657269, 0.37113685585616557, 0.37588512334090834, 0.36394377403527384, 0.3778515782612744, 0.3680674322013193, 0.3668903803131991, 0.3716225937329151, 0.3578561065119058, 0.36195920136537263, 0.3717303690435424, 0.3762762685139711, 0.369865399447665, 0.37904209140125833, 0.37714964370546317, 0.38468686117821965, 0.37726673635413355, 0.3793435428980835, 0.3753760347818449]

        ratios = [0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.15, 0.2]
        lsm_ratios_delays = [6.329736842105263, 5.296631578947369, 8.731871052631579, 11.22911447368421, 14.833186842105263, 15.850073684210528, 16.644891666666666, 15.070588596491229, 16.28684736842105, 15.767363157894739, 16.992230701754387, 13.904795614035086, 13.871193859649123, 16.36712192982456, 15.09846798245614]
        no_lsm_ratios_delays = [7.4, 8.09, 8.83, 18.76, 37.08, 45.34, 90.25, 200, 200, 200, 200, 200, 200, 200, 200]

        transaction_nums = []
        num = 35
        while num <= 50000:
            transaction_nums.append(num)
            if num < 100:
                num += 35
            elif num < 1000:
                num += 105
            elif num < 10000:
                num += 350
            elif num <= 50000:
                num += 1050

        data1 = lsm_ratios_delays

        data2 = no_lsm_ratios_delays


        x = ratios
        window_size = 3
        smoothed_data1 = np.convolve(data1, np.ones(window_size) / window_size, mode='valid')
        smoothed_data2 = np.convolve(data2, np.ones(window_size) / window_size, mode='valid')
        smoothed_x = x[(window_size - 1) // 2: -(window_size - 1) // 2]  # Adjust x values accordingly

        # Plot the original and smoothed data
        plt.plot(smoothed_x, smoothed_data1, color='red', linestyle='-', label='LSM', marker='o')
        plt.plot(smoothed_x, smoothed_data2, color='blue', linestyle='--', label='No LSM', marker='^')
        # Add labels and legend
        plt.ylim(0, 100)
        plt.yticks(np.linspace(0, 100, 11))
        plt.xlabel('Average Payment Amount to Starting Balance Ratio')
        plt.ylabel('Average Delay per Payment (minutes)')
        plt.legend()
        plt.savefig('delay_ratio.png')
        # Show plot
        plt.show()

