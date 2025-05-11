# sync_notice.py
from typing import Any

from db_connect import get_mongo_client
from db_connect.get_psql_conn import get_psql_conn
from datetime import datetime
from decimal import Decimal
import psycopg2.extras


def to_int(v):
	try:
		return int(v) if v not in [None, "", "-"] else None
	except:
		return None


def to_decimal(v):
	try:
		return Decimal(v) if v not in [None, "", "-"] else None
	except:
		return None


def to_datetime(v):
	try:
		return datetime.strptime(v, "%Y-%m-%d %H:%M:%S") if v else None
	except:
		return None


def transform_document(doc: dict[str, Any]) -> dict[str, Any]:
	transformed = {
		"bidNtceNo": doc.get("bidNtceNo", ""),
		"bidNtceOrd": doc.get("bidNtceOrd", ""),
		"reNtceYn": doc.get("reNtceYn", ""),
		"rgstTyNm": doc.get("rgstTyNm", ""),
		"ntceKindNm": doc.get("ntceKindNm", ""),
		"intrbidYn": doc.get("intrbidYn", ""),
		"bidNtceDt": to_datetime(doc.get("bidNtceDt")),
		"refNo": doc.get("refNo", ""),
		"bidNtceNm": doc.get("bidNtceNm", ""),
		"ntceInsttCd": doc.get("ntceInsttCd", ""),
		"ntceInsttNm": doc.get("ntceInsttNm", ""),
		"dminsttCd": doc.get("dminsttCd", ""),
		"dminsttNm": doc.get("dminsttNm", ""),
		"bidMethdNm": doc.get("bidMethdNm", ""),
		"cntrctCnclsMthdNm": doc.get("cntrctCnclsMthdNm", ""),
		"ntceInsttOfclNm": doc.get("ntceInsttOfclNm", ""),
		"ntceInsttOfclTelNo": doc.get("ntceInsttOfclTelNo", ""),
		"ntceInsttOfclEmailAdrs": doc.get("ntceInsttOfclEmailAdrs", ""),
		"exctvNm": doc.get("exctvNm", ""),
		"bidQlfctRgstDt": to_datetime(doc.get("bidQlfctRgstDt")),
		"cmmnSpldmdAgrmntRcptdocMethd": doc.get("cmmnSpldmdAgrmntRcptdocMethd", ""),
		"cmmnSpldmdAgrmntClseDt": doc.get("cmmnSpldmdAgrmntClseDt", ""),
		"cmmnSpldmdCorpRgnLmtYn": doc.get("cmmnSpldmdCorpRgnLmtYn", ""),
		"bidBeginDt": to_datetime(doc.get("bidBeginDt")),
		"bidClseDt": to_datetime(doc.get("bidClseDt")),
		"opengDt": to_datetime(doc.get("opengDt")),
		"ntceSpecDocUrl1": doc.get("ntceSpecDocUrl1", ""),
		"ntceSpecDocUrl2": doc.get("ntceSpecDocUrl2", ""),
		"ntceSpecDocUrl3": doc.get("ntceSpecDocUrl3", ""),
		"ntceSpecDocUrl4": doc.get("ntceSpecDocUrl4", ""),
		"ntceSpecDocUrl5": doc.get("ntceSpecDocUrl5", ""),
		"ntceSpecDocUrl6": doc.get("ntceSpecDocUrl6", ""),
		"ntceSpecDocUrl7": doc.get("ntceSpecDocUrl7", ""),
		"ntceSpecDocUrl8": doc.get("ntceSpecDocUrl8", ""),
		"ntceSpecDocUrl9": doc.get("ntceSpecDocUrl9", ""),
		"ntceSpecDocUrl10": doc.get("ntceSpecDocUrl10", ""),
		"ntceSpecFileNm1": doc.get("ntceSpecFileNm1", ""),
		"ntceSpecFileNm2": doc.get("ntceSpecFileNm2", ""),
		"ntceSpecFileNm3": doc.get("ntceSpecFileNm3", ""),
		"ntceSpecFileNm4": doc.get("ntceSpecFileNm4", ""),
		"ntceSpecFileNm5": doc.get("ntceSpecFileNm5", ""),
		"ntceSpecFileNm6": doc.get("ntceSpecFileNm6", ""),
		"ntceSpecFileNm7": doc.get("ntceSpecFileNm7", ""),
		"ntceSpecFileNm8": doc.get("ntceSpecFileNm8", ""),
		"ntceSpecFileNm9": doc.get("ntceSpecFileNm9", ""),
		"ntceSpecFileNm10": doc.get("ntceSpecFileNm10", ""),
		"rbidPermsnYn": doc.get("rbidPermsnYn", ""),
		"pqApplDocRcptMthdNm": doc.get("pqApplDocRcptMthdNm", ""),
		"pqApplDocRcptDt": doc.get("pqApplDocRcptDt", ""),
		"arsltApplDocRcptMthdNm": doc.get("arsltApplDocRcptMthdNm", ""),
		"arsltApplDocRcptDt": doc.get("arsltApplDocRcptDt", ""),
		"jntcontrctDutyRgnNm1": doc.get("jntcontrctDutyRgnNm1", ""),
		"jntcontrctDutyRgnNm2": doc.get("jntcontrctDutyRgnNm2", ""),
		"jntcontrctDutyRgnNm3": doc.get("jntcontrctDutyRgnNm3", ""),
		"rgnDutyJntcontrctRt": doc.get("rgnDutyJntcontrctRt", ""),
		"dtlsBidYn": doc.get("dtlsBidYn", ""),
		"bidPrtcptLmtYn": doc.get("bidPrtcptLmtYn", ""),
		"prearngPrceDcsnMthdNm": doc.get("prearngPrceDcsnMthdNm", ""),
		"totPrdprcNum": to_int(doc.get("totPrdprcNum")),
		"drwtPrdprcNum": to_int(doc.get("drwtPrdprcNum")),
		"bdgtAmt": to_int(doc.get("bdgtAmt")),
		"presmptPrce": to_int(doc.get("presmptPrce")),
		"govsplyAmt": to_int(doc.get("govsplyAmt")),
		"aplBssCntnts": doc.get("aplBssCntnts", ""),
		"indstrytyEvlRt": doc.get("indstrytyEvlRt", ""),
		"mainCnsttyNm": doc.get("mainCnsttyNm", ""),
		"mainCnsttyCnstwkPrearngAmt": doc.get("mainCnsttyCnstwkPrearngAmt", ""),
		"incntvRgnNm1": doc.get("incntvRgnNm1", ""),
		"incntvRgnNm2": doc.get("incntvRgnNm2", ""),
		"incntvRgnNm3": doc.get("incntvRgnNm3", ""),
		"incntvRgnNm4": doc.get("incntvRgnNm4", ""),
		"opengPlce": doc.get("opengPlce", ""),
		"dcmtgOprtnDt": doc.get("dcmtgOprtnDt", ""),
		"dcmtgOprtnPlce": doc.get("dcmtgOprtnPlce", ""),
		"contrctrcnstrtnGovsplyMtrlAmt": to_int(doc.get("contrctrcnstrtnGovsplyMtrlAmt")),
		"govcnstrtnGovsplyMtrlAmt": to_int(doc.get("govcnstrtnGovsplyMtrlAmt")),
		"bidNtceDtlUrl": doc.get("bidNtceDtlUrl", ""),
		"bidNtceUrl": doc.get("bidNtceUrl", ""),
		"bidPrtcptFeePaymntYn": doc.get("bidPrtcptFeePaymntYn", ""),
		"bidPrtcptFee": doc.get("bidPrtcptFee", ""),
		"bidGrntymnyPaymntYn": doc.get("bidGrntymnyPaymntYn", ""),
		"crdtrNm": doc.get("crdtrNm", ""),
		"cmmnSpldmdCnum": doc.get("cmmnSpldmdCnum", ""),
		"untyNtceNo": doc.get("untyNtceNo", ""),
		"sptDscrptDocUrl1": doc.get("sptDscrptDocUrl1", ""),
		"sptDscrptDocUrl2": doc.get("sptDscrptDocUrl2", ""),
		"sptDscrptDocUrl3": doc.get("sptDscrptDocUrl3", ""),
		"sptDscrptDocUrl4": doc.get("sptDscrptDocUrl4", ""),
		"sptDscrptDocUrl5": doc.get("sptDscrptDocUrl5", ""),
		"subsiCnsttyNm1": doc.get("subsiCnsttyNm1", ""),
		"subsiCnsttyNm2": doc.get("subsiCnsttyNm2", ""),
		"subsiCnsttyNm3": doc.get("subsiCnsttyNm3", ""),
		"subsiCnsttyNm4": doc.get("subsiCnsttyNm4", ""),
		"subsiCnsttyNm5": doc.get("subsiCnsttyNm5", ""),
		"subsiCnsttyNm6": doc.get("subsiCnsttyNm6", ""),
		"subsiCnsttyNm7": doc.get("subsiCnsttyNm7", ""),
		"subsiCnsttyNm8": doc.get("subsiCnsttyNm8", ""),
		"subsiCnsttyNm9": doc.get("subsiCnsttyNm9", ""),
		"subsiCnsttyIndstrytyEvlRt1": doc.get("subsiCnsttyIndstrytyEvlRt1", ""),
		"subsiCnsttyIndstrytyEvlRt2": doc.get("subsiCnsttyIndstrytyEvlRt2", ""),
		"subsiCnsttyIndstrytyEvlRt3": doc.get("subsiCnsttyIndstrytyEvlRt3", ""),
		"subsiCnsttyIndstrytyEvlRt4": doc.get("subsiCnsttyIndstrytyEvlRt4", ""),
		"subsiCnsttyIndstrytyEvlRt5": doc.get("subsiCnsttyIndstrytyEvlRt5", ""),
		"subsiCnsttyIndstrytyEvlRt6": doc.get("subsiCnsttyIndstrytyEvlRt6", ""),
		"subsiCnsttyIndstrytyEvlRt7": doc.get("subsiCnsttyIndstrytyEvlRt7", ""),
		"subsiCnsttyIndstrytyEvlRt8": doc.get("subsiCnsttyIndstrytyEvlRt8", ""),
		"subsiCnsttyIndstrytyEvlRt9": doc.get("subsiCnsttyIndstrytyEvlRt9", ""),
		"cmmnSpldmdMethdCd": doc.get("cmmnSpldmdMethdCd", ""),
		"cmmnSpldmdMethdNm": doc.get("cmmnSpldmdMethdNm", ""),
		"stdNtceDocUrl": doc.get("stdNtceDocUrl", ""),
		"brffcBidprcPermsnYn": doc.get("brffcBidprcPermsnYn", ""),
		"cnsttyAccotShreRateList": doc.get("cnsttyAccotShreRateList", ""),
		"cnstrtnAbltyEvlAmtList": doc.get("cnstrtnAbltyEvlAmtList", ""),
		"dsgntCmptYn": doc.get("dsgntCmptYn", ""),
		"arsltCmptYn": doc.get("arsltCmptYn", ""),
		"pqEvalYn": doc.get("pqEvalYn", ""),
		"ntceDscrptYn": doc.get("ntceDscrptYn", ""),
		"rsrvtnPrceReMkngMthdNm": doc.get("rsrvtnPrceReMkngMthdNm", ""),
		"mainCnsttyPresmptPrce": doc.get("mainCnsttyPresmptPrce", ""),
		"orderPlanUntyNo": doc.get("orderPlanUntyNo", ""),
		"sucsfbidLwltRate": to_decimal(doc.get("sucsfbidLwltRate")),
		"rgstDt": to_datetime(doc.get("rgstDt")),
		"bfSpecRgstNo": doc.get("bfSpecRgstNo", ""),
		"sucsfbidMthdCd": doc.get("sucsfbidMthdCd", ""),
		"sucsfbidMthdNm": doc.get("sucsfbidMthdNm", ""),
		"chgDt": doc.get("chgDt", ""),
		"dminsttOfclEmailAdrs": doc.get("dminsttOfclEmailAdrs", ""),
		"indstrytyLmtYn": doc.get("indstrytyLmtYn", ""),
		"cnstrtsiteRgnNm": doc.get("cnstrtsiteRgnNm", ""),
		"rgnDutyJntcontrctYn": doc.get("rgnDutyJntcontrctYn", ""),
		"chgNtceRsn": doc.get("chgNtceRsn", ""),
		"rbidOpengDt": doc.get("rbidOpengDt", ""),
		"ciblAplYn": doc.get("ciblAplYn", ""),
		"mtltyAdvcPsblYn": doc.get("mtltyAdvcPsblYn", ""),
		"mtltyAdvcPsblYnCnstwkNm": doc.get("mtltyAdvcPsblYnCnstwkNm", ""),
		"VAT": doc.get("VAT", ""),
		"indutyVAT": doc.get("indutyVAT", ""),
		"indstrytyMfrcFldEvlYn": doc.get("indstrytyMfrcFldEvlYn", ""),
		"bidWgrnteeRcptClseDt": doc.get("bidWgrnteeRcptClseDt", ""),
		"bssamt": to_int(doc.get("bssamt")),
		"bssamtOpenDt": to_datetime(doc.get("bssamtOpenDt")),
		"rsrvtnPrceRngBgnRate": to_decimal(doc.get("rsrvtnPrceRngBgnRate")),
		"rsrvtnPrceRngEndRate": to_decimal(doc.get("rsrvtnPrceRngEndRate")),
		"evlBssAmt": to_int(doc.get("evlBssAmt")),
		"dfcltydgrCfcnt": to_decimal(doc.get("dfcltydgrCfcnt")),
		"etcGnrlexpnsBssRate": to_decimal(doc.get("etcGnrlexpnsBssRate")),
		"gnrlMngcstBssRate": to_decimal(doc.get("gnrlMngcstBssRate")),
		"prftBssRate": to_decimal(doc.get("prftBssRate")),
		"lbrcstBssRate": to_decimal(doc.get("lbrcstBssRate")),
		"sftyMngcst": to_int(doc.get("sftyMngcst")),
		"sftyChckMngcst": to_int(doc.get("sftyChckMngcst")),
		"rtrfundNon": to_int(doc.get("rtrfundNon")),
		"envCnsrvcst": to_int(doc.get("envCnsrvcst")),
		"scontrctPayprcePayGrntyFee": to_int(doc.get("scontrctPayprcePayGrntyFee")),
		"mrfnHealthInsrprm": to_int(doc.get("mrfnHealthInsrprm")),
		"npnInsrprm": to_int(doc.get("npnInsrprm")),
		"rmrk1": doc.get("rmrk1", ""),
		"rmrk2": doc.get("rmrk2", ""),
		"odsnLngtrmrcprInsrprm": to_int(doc.get("odsnLngtrmrcprInsrprm")),
		"usefulAmt": to_int(doc.get("usefulAmt")),
		"inptDt": to_datetime(doc.get("inptDt")),
		"bidPrceCalclAYn": doc.get("bidPrceCalclAYn", "")[:1],
		"bssAmtPurcnstcst": doc.get("bssAmtPurcnstcst", ""),
		"qltyMngcst": to_int(doc.get("qltyMngcst")),
		"qltyMngcstAObjYn": doc.get("qltyMngcstAObjYn", "")[:1],
	}
	return transformed


def sync_notice_data():
	with get_mongo_client() as mongo_client:
		mongo_db = mongo_client.get_database("gfcon_raw")
		mongo_default = mongo_db.get_collection("입찰공고정보서비스.입찰공고목록정보에대한공사조회")
		mongo_bssAmt = mongo_db.get_collection("입찰공고정보서비스.입찰공고목록정보에대한공사기초금액조회")

		with get_psql_conn() as pg_conn:
			with pg_conn.cursor() as cur:
				total_doc_count = mongo_default.count_documents({})


def test():
	with get_mongo_client() as mongo_client:
		mongo_db = mongo_client.get_database("gfcon_raw")
		mongo_default = mongo_db.get_collection("입찰공고정보서비스.입찰공고목록정보에대한공사조회")

		count = mongo_default.count_documents({})
		print(count)


test()
