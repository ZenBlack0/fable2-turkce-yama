import json
import os

COMMON_TR = {
    "txtBankTitle": "Bankacılık",
    "txtBankGold": "Altın",
    "txtBankChips": "Fişler",
    "txtBankDebt": "Borç",
    "txtBankCreditLimit": "Kredi Limiti",
    "txtBankQuickChips": "Hızlı Fişler: $chips",
    "txtBankAmount": "$value",
    "txtBankGetChips": "Fiş Al",
    "txtBankGetChipsTitle": "Fiş Al",
    "txtBankGetChipsInstructions": "Ödünç alınacak fiş miktarını seçmek için sol çubuğu kullanın",
    "txtBankGetChipsTip": "İpucu: Kredi limitinize kadar istediğiniz zaman fiş ödünç alabilirsiniz. Ancak aşırı borç Fable® II dünyasında başınızı derde sokabilir...",
    "txtBankPayDebtWithChips": "Borcu Fişlerle Öde",
    "txtBankPayDebtWithChipsTitle": "Borcu Fişlerle Öde",
    "txtBankPayDebtWithChipsInstructions": "Geri ödenecek borç miktarını seçmek için sol çubuğu kullanın",
    "txtBankPayDebtWithChipsTip": "İpucu: İstediğiniz zaman borcunuzu fişlerle ödeyebilirsiniz. Aşırı borcun Fable® II dünyasında başınızı derde sokabileceğini unutmayın...",
    "txtBankPayDebtWithGold": "Borcu Öde",
    "txtBankPayDebtWithGoldTitle": "Borcu Altınla Öde",
    "txtBankPayDebtWithGoldInstructions": "Geri ödenecek borç miktarını seçmek için sol çubuğu kullanın",
    "txtBankPayDebtWithGoldTip": "İpucu: İstediğiniz zaman borcunuzu altınla ödeyebilirsiniz. Aşırı borcun Fable® II dünyasında başınızı derde sokabileceğini unutmayın...",
    "txtBankCashOut": "Nakit Al ve Oyundan Çık",
    "txtBankSelectAmount": "Miktarı Seç",
    "txtBankConfirm": "Onayla",
    "txtBankCancel": "İptal",
    "txtBankSelect": "Seç",
    "txtBankResumeGame": "Oyuna Dön",
    "txtBankResume": "Devam Et",
    "txtBankChipsLabel": "Fişler:",
    "txtBankGoldLabel": "Altın:",
    "txtBankDebtLabel": "Borç:",
    "txtDebtSliderLabel": "Geri Öde:",
    "txtBorrowSliderLabel": "Ödünç Al:",
    "txtBankChipsValue": "$value",
    "txtBankGoldValue": "$value",
    "txtBankDebtValue": "$value",
    "txtSliderValue": "$value",
    "txtShimTitle": "Fable II Pub Oyunları",
    "txtShimTutorial": "Eğitim",
    "txtShimMerge": "Müdavimle Birleştir",
    "txtShimLeave": "Masadan Ayrıl",
    "txtShimConfirm": "Seç",
    "txtShimCancel": "Geri",
    "txtShimMergeTitle": "Müdavimle Birleştir",
    "txtShimMergeButton": "Birleştir",
    "txtShimMergeCancel": "İptal",
    "txtShimMergeSuccess": "Seçilen Müdavim mevcut karakterinizle başarıyla birleştirildi. Eski Müdavim silindi.",
    "txtShimMergeFailed": "Bu karakterler başarıyla birleştirilemedi. Orijinal istatistikleri ve envanterleri değiştirilmedi.",
    "txtShimMergeConfirm": "Birleştirmeyi Onayla",
    "txtShimMergeMessage": "Birleştirme 500 altına mal olur.\\n\\nBirleştirmeden sonra $NAME1 şunlara sahip olacak:\\n$GOLD altın\\n$DEBT borç\\n$POINTS puan\\n\\n$NAME2 silinecektir.\\nBu işlem geri alınamaz.",
    "txtShimPaused": "Duraklatıldı",
    "txtShimPauseResume": "Pub Oyununa Dön",
    "txtShimPauseHelpAndOptions": "Yardım ve Seçenekler",
    "txtShimPauseHelp": "Yardım",
    "txtShimPauseControls": "Kontroller",
    "txtShimPauseSettings": "Ayarlar",
    "txtShimPauseExit": "Pub Oyunundan Çık",
    "txtShimPauseTutorialExit": "Eğitimden Çık",
    "txtShimControlsTitle": "Kontroller",
    "txtShimControlsKeystoneBtnA": "Bahsi Artır",
    "txtShimControlsKeystoneBtnB": "Bahsi Azalt",
    "txtShimControlsKeystoneBtnX": "Zar At",
    "txtShimControlsKeystoneBtnY": "Banka",
    "txtShimControlsKeystoneLeftStick": "İmleci Taşı",
    "txtShimControlsKeystoneRightStick": "Bahsi Artır/Azalt",
    "txtShimControlsKeystoneLeftTrigger": "Oranlar",
    "txtShimControlsKeystoneLeftButton": "Maksimum Bahis",
    "txtShimControlsKeystoneRightTrigger": "Sıralama/İstatistikler",
    "txtShimControlsKeystoneRightButton": "Son Bahisleri Tekrarla",
    "txtShimControlsFortunesTowerBtnA": "Dağıt",
    "txtShimControlsFortunesTowerBtnB": "Teklifi Al",
    "txtShimControlsFortunesTowerBtnX": "Kullanılmıyor",
    "txtShimControlsFortunesTowerBtnY": "Banka",
    "txtShimControlsFortunesTowerLeftStick": "Bahsi Artır/Azalt",
    "txtShimControlsFortunesTowerRightStick": "Bahsi Artır/Azalt",
    "txtShimControlsFortunesTowerLeftTrigger": "İpuçları",
    "txtShimControlsFortunesTowerRightTrigger": "Sıralama/İstatistikler",
    "txtShimControlsFortunesTowerLeftButton": "Maksimum Bahis",
    "txtShimControlsFortunesTowerRightButton": "Kullanılmıyor",
    "txtShimControlsSpinnerBoxBtnA": "Çevir",
    "txtShimControlsSpinnerBoxBtnB": "Kullanılmıyor",
    "txtShimControlsSpinnerBoxBtnX": "Kullanılmıyor",
    "txtShimControlsSpinnerBoxBtnY": "Banka",
    "txtShimControlsSpinnerBoxLeftStick": "Bahsi Artır/Azalt",
    "txtShimControlsSpinnerBoxRightStick": "Bahsi Artır/Azalt",
    "txtShimControlsSpinnerBoxLeftTrigger": "Ödemeler",
    "txtShimControlsSpinnerBoxRightTrigger": "Sıralama/İstatistikler",
    "txtShimControlsSpinnerBoxLeftButton": "Maksimum Bahis",
    "txtShimControlsSpinnerBoxRightButton": "Kullanılmıyor",
    "txtSounds": "Sesler",
    "txtMusic": "Müzik",
    "txtRestoreDefaults": "Varsayılanlara Sıfırla",
    "txtPause": "Duraklat",
    "txtCashOutTitle": "Nakit Alındı",
    "txtCashOutUpGold": "Tebrikler, $value altın kazandınız!",
    "txtCashOutEvenGold": "Güzel çaba! Başabaş kaldınız!",
    "txtCashOutDownGold": "Maalesef $value altın kaybettiniz.\\nBir dahaki sefere bol şans!",
    "txtCashOutGold": "Altın: $value",
    "txtCashOutDebt": "Borç: $value",
    "txtCashOutPointsToNextLevel": "Sonraki Seviyeye Kalan Puan: $value",
    "txtCashOutConfirm": "Devam Et",
    "txtCashOutHint0": "Faydalı İpucu: Herhangi bir turnuvada ilk beşe girenler nakit ödülün yanı sıra eşsiz bir Fable® II eşyası kazanır!"
}

# Load original common strings and merge
with open("translation/pubgames_src/common.json", "r", encoding="utf-8") as f:
    items = json.load(f)

final_common = {}
for it in items:
    k = it["id"]
    txt = it["text"]
    if k in COMMON_TR:
        final_common[k] = COMMON_TR[k]
    else:
        final_common[k] = txt

os.makedirs("translation/pubgames_tr", exist_ok=True)
with open("translation/pubgames_tr/common.json", "w", encoding="utf-8") as f:
    json.dump(final_common, f, ensure_ascii=False, indent=2)

print(f"Generated {len(final_common)} translations for common")
