import json
import os

KEYSTONE_TR = {
    "txtGameName": "Kilit Taşı",
    "idKeystoneLocTest": "KİLİT TAŞI test yerelleştirme dosyası",
    "txtStartInnerBet": "İç Bahisler",
    "txtRoll": "Zar At",
    "txtIncreaseBet": "Bahis Koy",
    "txtDecreaseBet": "Bahsi Kaldır",
    "txtMoveCursor": "Taşı",
    "txtChangeBet": "Bahsi Ayarla",
    "txtPlaceArchBet": "Oyuna başlamak için en az bir Kemer bahsi koyun.",
    "txtPlaceArchBetMore": "Daha fazla Kemer bahsi koyabilir veya iç bahislere geçebilirsiniz.",
    "txtPlaceArchBetMove": "İç Bahisler",
    "txtContinueGame": "Devam Et",
    "txtEmptySeat": "Boş Koltuk",
    "txtKeystoneSpace": "Kilit Taşı",
    "txtPairSpace": "Çift",
    "txtTripsSpace": "Üçlü",
    "txtStraightSpace": "Seri",
    "txtArchBet": "Kemer Bahsi:",
    "txtArchWin": "Kazanç:",
    "txtInsideBet": "İç Bahis:",
    "txtInsideWin": "Kazanç:",
    "txtArchRisk": "Kemer Riski:",
    "txtInsideRisk": "İç Risk:",
    "txtChipsAtRisk": "Toplam Risk:",
    "txtWin": "Kazanç:",
    "txtExposureWarning": "Risk altındaki tüm bahisleri karşılayacak yeterli fişiniz yok. Ya bazı fişleri kaldırın ya da daha fazla fiş ödünç alın.\\n\\nDaha fazla fiş ödünç almak ister misiniz?",
    "txtArchBetValue": "$value",
    "txtArchWinValue": "$value",
    "txtInsideBetValue": "$value",
    "txtInsideWinValue": "$value",
    "txtChipTotal": "$value",
    "txtPlayerName": "$value",
    "txtStackValue": "$value",
    "txtJackpot": "Büyük İkramiye",
    "txtSpace_out3": "Kemer 3",
    "txtSpace_out4": "Kemer 4",
    "txtSpace_out5": "Kemer 5",
    "txtSpace_out6": "Kemer 6",
    "txtSpace_out7": "Kemer 7",
    "txtSpace_out8": "Kemer 8",
    "txtSpace_out9": "Kemer 9",
    "txtSpace_out10": "Kemer 10",
    "txtSpace_out11": "Kemer 11",
    "txtSpace_out12": "Kemer 12",
    "txtSpace_out13": "Kemer 13",
    "txtSpace_out14": "Kemer 14",
    "txtSpace_out15": "Kemer 15",
    "txtSpace_out16": "Kemer 16",
    "txtSpace_out17": "Kemer 17",
    "txtSpace_out18": "Kemer 18",
    "txtSpace_in3": "İç 3",
    "txtSpace_in4": "İç 4",
    "txtSpace_in5": "İç 5",
    "txtSpace_in6": "İç 6",
    "txtSpace_in7": "İç 7",
    "txtSpace_in8": "İç 8",
    "txtSpace_in9": "İç 9",
    "txtSpace_in10": "İç 10",
    "txtSpace_in11": "İç 11",
    "txtSpace_in12": "İç 12",
    "txtSpace_in13": "İç 13",
    "txtSpace_in14": "İç 14",
    "txtSpace_in15": "İç 15",
    "txtSpace_in16": "İç 16",
    "txtSpace_in17": "İç 17",
    "txtSpace_in18": "İç 18",
    "txtSpace_custom": "Özel",
    "txtGameHelpTitle": "Kilit Taşı Nasıl Oynanır",
    "txtGameHelpSection1": "Kemer",
    "txtGameHelpText1": "Kilit Taşı, oyuncuların üç zarın sonucuna bahis oynadığı bir pub oyunudur. Oyun tahtası taşlardan oluşan bir Kemer şeklinde düzenlenmiştir. Zarlar atıldıkça kemerden taşlar çıkarılır. Kilit taşları çıkarıldığında oyun sona erer.",
    "txtGameHelpSection2": "Kemer Bahisleri",
    "txtGameHelpText2": "Her oyunun başında en az bir Kemer bahsi koymalısınız. Kemer bahisleri, o taş kemerden çıkarılana kadar masada kalır. Taş çıkarıldığında bahsiniz ödenir.",
    "txtGameHelpSection3": "İç Bahisler",
    "txtGameHelpText3": "İç bahisler tek bir zar atışının sonucuna oynanır. Her atıştan sonra kazanan iç bahisler ödenir ve kaybedenler toplanır.",
    "txtGameHelpSection4": "Kilit Taşı Kuralı",
    "txtGameHelpText4": "Tahtanın tepesindeki taşa Kilit Taşı denir. Kilit Taşı çıkarıldığında kemer çöker ve oyun sona erer. Masada kalan tüm Kemer bahisleri kaybedilir.",
    "txtGameHelpSection5": "Strateji",
    "txtGameHelpText5": "Kilit Taşı oynamanın anahtarı, Kemer bahislerinizin potansiyel kazancı ile Kilit Taşının düşme riski arasındaki dengeyi kurmaktır.",
    "txtTutorialHeader0": "Kilit Taşı'na Hoş Geldiniz!",
    "txtTutorialInfo0": "Kilit Taşı, zarlarla oynanan heyecan verici bir şans oyunudur. Üç zar atılır ve sonuçlara göre Kemer üzerindeki taşlar kaldırılır.",
    "txtTutorialHeader1": "Kemer Bahsi Koyma",
    "txtTutorialInfo1": "Oyuna başlamak için bir Kemer bahsi koyun. Kemerdeki bir sayıyı seçin ve bahsinizi yerleştirin.",
    "txtTutorialHeader2": "Zar Atma",
    "txtTutorialInfo2": "Şimdi zarları atın. Zarların toplamı seçtiğiniz taşa denk gelirse taş çıkarılır ve kazanırsınız!",
    "txtTournamentTitle": "Kilit Taşı Turnuvası",
    "txtTournamentPrize1": "Bir Saç Modeli\\nKartı kazandınız!",
    "txtTournamentPrize2": "Köpek Eğitimi:\\nTakla Atma kazandınız!",
    "txtTournamentPrize3": "Bir Kodaman\\nPaltosu kazandınız!",
    "txtTournamentPrize4": "Bir İrade\\nİksiri kazandınız!",
    "txtTournamentPrize5": "Bir Şampiyona\\nTabancası kazandınız!",
    "txtShimPlay": "Kilit Taşı Oyna"
}

# Load original keystone strings and fill anything missing
with open("translation/pubgames_src/keystone.json", "r", encoding="utf-8") as f:
    items = json.load(f)

final_keystone = {}
for it in items:
    k = it["id"]
    txt = it["text"]
    if k in KEYSTONE_TR:
        final_keystone[k] = KEYSTONE_TR[k]
    else:
        # Default or literal token
        final_keystone[k] = txt

os.makedirs("translation/pubgames_tr", exist_ok=True)
with open("translation/pubgames_tr/keystone.json", "w", encoding="utf-8") as f:
    json.dump(final_keystone, f, ensure_ascii=False, indent=2)

print(f"Generated {len(final_keystone)} translations for keystone")
