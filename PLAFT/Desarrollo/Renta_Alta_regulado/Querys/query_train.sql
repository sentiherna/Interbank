CREATE TABLE "disc_comercial"."platf_renta_alta_train_V1" WITH (
     format = 'parquet',
  external_location = 's3://ibk-discovery-comercial-us-east-1-654654352211-data/discovery/comercial/sanherna/PLAFT/PN/RENTA_ALTA/DATA_INFERENCIA/INFERENCIA/',
  partitioned_by = ARRAY [ 'codmes' ]
) AS

WITH pd AS (
    SELECT DISTINCT
        -- Identificadores
        key_value,
        cod_cli,
        cod_tip_doc,
        date_format(
            date_parse(CAST(cod_mes AS varchar), '%Y%m') - interval '1' month,
            '%Y%m'
        ) AS codmes_lag1,
        CAST(cod_mes AS INTEGER) AS cod_mes,

        -- Fechas
        TRY_CAST(fec_constitucion AS DATE) AS fec_constitucion,

        -- Monetarios
        TRY_CAST(mto_pas_soles AS DOUBLE) AS mto_pas_soles,
        TRY_CAST(imp_trx_abonosefect_6m AS DOUBLE) AS imp_trx_abonosefect_6m,
        TRY_CAST(imp_trx_cargosefe_6m AS DOUBLE) AS imp_trx_cargosefe_6m,
        TRY_CAST(avg_trx_cargostot_3m AS DOUBLE) AS avg_trx_cargostot_3m,
        TRY_CAST(max_trx_abonos_3m AS DOUBLE) AS max_trx_abonos_3m,

        -- Cantidades
        TRY_CAST(cnt_trx_cargostot_3m AS INTEGER) AS cnt_trx_cargostot_3m,

        -- Promedios / ratios
        TRY_CAST(cnt_trx_abonospromtot_3m AS DOUBLE) AS cnt_trx_abonospromtot_3m,
        TRY_CAST(rat_trx_abonosefectot_1m AS DOUBLE) AS rat_trx_abonosefectot_1m,
        TRY_CAST(rat_trx_abonosefectot_3m AS DOUBLE) AS rat_trx_abonosefectot_3m,
        TRY_CAST(rat_trx_abonosefectot_9m AS DOUBLE) AS rat_trx_abonosefectot_9m,
        TRY_CAST(rat_mntcrgsefetot_1m AS DOUBLE) AS rat_mntcrgsefetot_1m,

        -- Demográficas / antigüedad
        TRY_CAST(num_edad_constitucion AS INTEGER) AS num_edad_constitucion,
        TRY_CAST(num_antiguedad AS INTEGER) AS num_antiguedad,

        -- Riesgo
        TRY_CAST(desc_nivel_rsg_lsb_tot AS DOUBLE) AS desc_nivel_rsg_lsb_tot,

        -- Actividad mensual
        TRY_CAST(cnt_meses_siningresos_12m AS INTEGER) AS cnt_meses_siningresos_12m,
        TRY_CAST(cnt_meses_sinegresos_12m AS INTEGER) AS cnt_meses_sinegresos_12m,

        -- Ubicación / segmentación
        desc_provincia,
        desc_departamento,
        cod_ubigeo_cd,
        cod_sectorista_id,
        cod_ciiu_v4,

        -- Flags (string/bool → 0/1)
       flg_casos_hist,
       flg_vrcn_abonos_5m_1m,
       flg_vrcn_efe_cargos_5m_1m,

        -- Conteos
        cnt_ro_debajo_umbral,
         -- Perfil económico
        mto_fact_declarado_sunat,
        TRY_CAST(avg_cp_men_ing_12m AS DOUBLE) AS avg_cp_men_ing_12m,
        TRY_CAST(avg_cpmenegr_12m AS DOUBLE) AS avg_cpmenegr_12m,
        TRY_CAST(max_mto_cpmening_12m AS DOUBLE) AS max_mto_cpmening_12m,
        TRY_CAST(max_mto_cpegrmen_12m AS DOUBLE) AS max_mto_cpegrmen_12m,

        -- Exterior
        flg_al_ext_12m,
        flg_del_ext_12m,
        TRY_CAST(cnt_trx_sinenv_alext_12m AS INTEGER) AS cnt_trx_sinenv_alext_12m,
        TRY_CAST(cnt_trx_al_ext_1000_12m AS INTEGER) AS cnt_trx_al_ext_1000_12m,
        TRY_CAST(mto_al_ext_12m AS DOUBLE) AS mto_al_ext_12m,
        TRY_CAST(mto_del_ext_12m AS DOUBLE) AS mto_del_ext_12m,

        -- Reputacional / antecedentes
        flg_pep,
        cod_rsg_pep,
        flg_activo_pep,
        TRY_CAST(cnt_noticias AS INTEGER) AS cnt_noticias,
        flg_ros_12m,
        flg_alerta_12m,
        TRY_CAST(cnt_alerta_hist AS INTEGER) AS cnt_alerta_hist,
        TRY_CAST(cnt_ros_hist AS INTEGER) AS cnt_ros_hist,

        -- KYC
        flg_kyc_12m,
        flg_kyc_hist,
        TRY_CAST(cnt_kyc_hist AS INTEGER) AS cnt_kyc_hist,
        -- ======================================================
        -- 🔹 ACELERACIÓN / CAMBIO DE COMPORTAMIENTO
        -- ======================================================
        TRY_CAST(imp_trx_abonostot_1m AS DOUBLE)
            / NULLIF(TRY_CAST(avg_trx_abonostot_6m AS DOUBLE), 0)
            AS rat_abonos_1m_vs_6m,

        TRY_CAST(imp_trx_cargostot_1m AS DOUBLE)
            / NULLIF(TRY_CAST(avg_trx_cargostot_6m AS DOUBLE), 0)
            AS rat_cargos_1m_vs_6m,


        -- ======================================================
        -- 🔹 CONCENTRACIÓN EN CONTRAPARTE
        -- ======================================================
        TRY_CAST(avg_cpmenegr_12m AS DOUBLE)
            / NULLIF(TRY_CAST(imp_trx_cargostot_6m AS DOUBLE), 0)
            AS rat_egr_princ_contraparte_12m,

        TRY_CAST(avg_cp_men_ing_12m AS DOUBLE)
            / NULLIF(TRY_CAST(imp_trx_abonostot_6m AS DOUBLE), 0)
            AS rat_ing_princ_contraparte_12m,


        -- ======================================================
        -- 🔹 NORMALIZACIÓN DE RIESGO
        -- ======================================================
        TRY_CAST(cnt_ros_hist AS DOUBLE)
            / NULLIF(TRY_CAST(cnt_trx_cargostot_3m AS DOUBLE), 0)
            AS rat_cntros_x_cnttrxegr_3m,

        TRY_CAST(cnt_alerta_hist AS DOUBLE)
            / NULLIF(TRY_CAST(num_antiguedad AS DOUBLE), 0)
            AS rat_alertas_antiguedad_1m,


        -- ======================================================
        -- 🔹 COHERENCIA ECONÓMICA
        -- ======================================================
        TRY_CAST(imp_trx_abonostot_6m AS DOUBLE)
            / NULLIF(TRY_CAST(mto_fact_declarado_sunat AS DOUBLE), 0)
            AS rat_ing_tot_x_factura_6m,

        TRY_CAST(mto_pas_soles AS DOUBLE)
            / NULLIF(TRY_CAST(imp_trx_abonostot_6m AS DOUBLE), 0)
            AS rat_pastot_x_ingtot_6m,


        -- ======================================================
        -- 🔹 EXPOSICIÓN AL EXTERIOR (PROPORCIONES)
        -- ======================================================
        TRY_CAST(mto_al_ext_12m AS DOUBLE)
            / NULLIF(TRY_CAST(imp_trx_cargostot_12m AS DOUBLE), 0)
            AS rat_egr_ext_x_egr_tot_12m,

        TRY_CAST(mto_del_ext_12m AS DOUBLE)
            / NULLIF(TRY_CAST(imp_trx_abonostot_12m AS DOUBLE), 0)
            AS rat_ing_ext_x_ing_tot_12m,


        -- ======================================================
        -- 🔹 COHERENCIA PEP / LSB
        -- ======================================================
        TRY_CAST(cod_rsg_pep AS DOUBLE)
            - TRY_CAST(desc_nivel_rsg_lsb_tot AS DOUBLE)
            AS gap_riesgo_pep_lsb

    FROM e_perm_aws.t_agg_alertas_plaft
    WHERE cod_mes between '202501' and  '202604'
    AND desc_subsegmento = 'Renta Alta'
),

target AS (
    SELECT 
        codunico,
        periodo_alerta,
        tipo_alerta_n2 ,
        MAX(calificacion_monitoreo) AS flg_alerta
    FROM e_perm_aws.t_alertas_plaft
    GROUP BY codunico, periodo_alerta, tipo_alerta_n2
),

-- =========================
-- 360 CLIENTE
-- =========================
pd_02 AS (
    SELECT
        key_value,
        codmes,
        MAX(edad) AS edad,
        MAX(ingreso_bruto) AS ingreso_bruto
    FROM e_perm_aws.v_aws_360_cliente_dia
    WHERE flg_fallecido = 'N'
      AND cod_tipo_documento = 1
      AND CAST(codmes AS INTEGER) BETWEEN 202501 AND 202604
    GROUP BY key_value, codmes
),

-- =========================
-- RCC AGG01
-- =========================
pd_05 AS (
    SELECT
        key_value,
        p_codmes,
        prom_lin_tc_rccsf_06m,
        lin_tcrrstsf03m,
        prm_usotcrrstsf03m,
        prm_lintcrallsf12m,
        prm_lintcrrstsf03m,
        cre_saltot_tc_rccsf_m02,
        prom_salvig_entprinc_tc_rccsf_03m,
        cre_salvig_tc_rccsf_m02,
        ind_max_salvig_tc_rccsf_06m,
        var_usotcrrstsf03m,
        ctd_prod_rccsf_m01,
        ind_min_salvig_tc_rccsf_06m,
        lintot_tc_rccsf_03m,
        prom_salvig_pp_rccsf_06m,
        salvig_pp_rccsf_06m,
        cre_pct_salvig_tc_rccsf_m03,
        prom_salvig_tc_rccsf_06m,
        cre_lin_tc_rccsf_m02,
        var_lintcrrstsf03m
    FROM e_perm_aws.tbl_rcc_agg01_allsf_mdl
    WHERE CAST(p_codmes AS INTEGER) BETWEEN 202501 AND 202603
),

-- =========================
-- PERFIL
-- =========================
pd_06 AS (
    SELECT
        key_value,
        p_codmes,
        rgn,
        tip_lvledu
    FROM e_perm_aws.tbl_per_inf_mdl
    WHERE CAST(p_codmes AS INTEGER) BETWEEN 202510 AND 202603
),

-- =========================
-- RIESGO
-- =========================
pd_07 AS (
    SELECT
        key_value,
        p_codmes,
        ing_brt,
        ind_lin_ing_tcr_ibk,
        cem
    FROM e_perm_aws.tbl_rsk_inf_mdl
    WHERE CAST(p_codmes AS INTEGER) BETWEEN 202501 AND 202603
),

-- =========================
-- RCC AGG02
-- =========================
pd_08 AS (
    SELECT
        key_value,
        p_codmes,
        AVG(sow_lnep1tcrallsfm01) AS sow_lnep1tcrallsfm01,
        AVG(sow_svep1actallsfm01) AS sow_svep1actallsfm01
    FROM e_perm_aws.tbl_rcc_agg02_allsf_mdl
    WHERE CAST(p_codmes AS INTEGER) BETWEEN 202501 AND 202603
    GROUP BY key_value, p_codmes
),

-- =========================
-- CAMPAÑAS
-- =========================
pd_09 AS (
    SELECT
        key_value,
        p_codmes,
        ctd_camptot06m,
        prm_camptot06m,
        max_camptot06m,
        min_camptot06m,
        rec_camptot06m
    FROM e_perm_aws.tbl_cmp_tot_inf_mdl
    WHERE tip_doc = '1'
      AND CAST(p_codmes AS INTEGER) BETWEEN 202501 AND 202603
),

-- =========================
-- CANALES
-- =========================
pd_10 AS (
    SELECT
        key_value,
        mes AS p_codmes,
        atm_monto,
        atm_frec,
        atm_recen,
        atm_trx_prom,
        atm_trx_ret_prom,
        atm_trx_dep,
        atm_trx_dep_prom,
        atm_trx_nmon_prom,
        atm_trx_nmon_prom2,
        atm_trx_nmon_min,
        atm_trx_con,
        atm_trx_con_prom,
        bpi_monto,
        bpi_trx_prom,
        bpi_trx_prom2,
        bpi_trx_nmon_prom,
        bpi_trx_nmon_prom2,
        bpi_trx_mon_prom,
        bpi_trx_mon_prom2,
        bpi_trx_mon_min,
        bpi_trx_mon_max,
        bpi_recen_mon,
        bpi_recen_nmon,
        grupo_final
    FROM e_perm_aws.v_seg_canales
    WHERE tipodocumento = '1'
      AND CAST(mes AS INTEGER) BETWEEN 202501 AND 202603
),

-- =========================
-- EDUCACIÓN (CORREGIDO)
-- =========================
pd_11 AS (
    SELECT
        key_value,
        p_codmes,
        lvl_edu
    FROM e_perm_aws.t_sentinel_rsk
    WHERE CAST(p_codmes AS INTEGER) BETWEEN 202501 AND 202603
),

-- =========================
-- SELECT FINAL
-- =========================

pd_100 as(

SELECT
CASE WHEN b.flg_alerta = '1' THEN 1 ELSE 0  END AS target_m,
a.key_value,
a.cod_cli AS codunico,
a.codmes_lag1,
a.cod_mes,
a.fec_constitucion,
a.mto_pas_soles,
a.imp_trx_abonosefect_6m,
a.imp_trx_cargosefe_6m,
a.avg_trx_cargostot_3m,
a.max_trx_abonos_3m,
a.cnt_trx_cargostot_3m,
a.cnt_trx_abonospromtot_3m,
a.rat_trx_abonosefectot_1m,
a.rat_trx_abonosefectot_3m,
a.rat_trx_abonosefectot_9m,
a.rat_mntcrgsefetot_1m,
a.num_edad_constitucion,
a.num_antiguedad,
a.desc_nivel_rsg_lsb_tot,
a.cnt_meses_siningresos_12m,
a.cnt_meses_sinegresos_12m,
a.desc_provincia,
a.desc_departamento,
a.cod_ubigeo_cd,
a.cod_sectorista_id,
a.cod_ciiu_v4,
a.flg_casos_hist,
a.flg_vrcn_abonos_5m_1m,
a.flg_vrcn_efe_cargos_5m_1m,
a.cnt_ro_debajo_umbral,
a.cnt_alerta_hist,
a.cnt_ros_hist,
a.mto_fact_declarado_sunat,
a.avg_cp_men_ing_12m,
a.avg_cpmenegr_12m,
a.max_mto_cpmening_12m,
a.max_mto_cpegrmen_12m,
a.flg_al_ext_12m,
a.flg_del_ext_12m,
a.cnt_trx_sinenv_alext_12m,
a.cnt_trx_al_ext_1000_12m,
a.mto_al_ext_12m,
a.mto_del_ext_12m,
a.flg_pep,
a.cod_rsg_pep,
a.flg_activo_pep,
a.cnt_noticias,
a.flg_ros_12m,
a.flg_alerta_12m,
a.flg_kyc_12m,
a.flg_kyc_hist,
a.cnt_kyc_hist,
a.rat_abonos_1m_vs_6m,
a.rat_cargos_1m_vs_6m,
a.rat_egr_princ_contraparte_12m,
a.rat_ing_princ_contraparte_12m,
a.rat_cntros_x_cnttrxegr_3m,
a.rat_alertas_antiguedad_1m,
a.rat_ing_tot_x_factura_6m,
a.rat_pastot_x_ingtot_6m,
a.rat_egr_ext_x_egr_tot_12m,
a.rat_ing_ext_x_ing_tot_12m,
a.gap_riesgo_pep_lsb,
b.tipo_alerta_n2,



    c.edad,
    c.ingreso_bruto,

    f.p_codmes,
    f.prom_lin_tc_rccsf_06m,
    f.lin_tcrrstsf03m,
    f.prm_usotcrrstsf03m,
    f.prm_lintcrallsf12m,
    f.prm_lintcrrstsf03m,
    f.cre_saltot_tc_rccsf_m02,
    f.prom_salvig_entprinc_tc_rccsf_03m,
    f.cre_salvig_tc_rccsf_m02,
    f.ind_max_salvig_tc_rccsf_06m,
    f.var_usotcrrstsf03m,
    f.ctd_prod_rccsf_m01,
    f.ind_min_salvig_tc_rccsf_06m,
    f.lintot_tc_rccsf_03m,
    f.prom_salvig_pp_rccsf_06m,
    f.salvig_pp_rccsf_06m,
    f.cre_pct_salvig_tc_rccsf_m03,
    f.prom_salvig_tc_rccsf_06m,
    f.cre_lin_tc_rccsf_m02,
    f.var_lintcrrstsf03m,

    g.rgn,
    g.tip_lvledu,

    h.ing_brt,
    h.ind_lin_ing_tcr_ibk,
    h.cem,

    i.sow_lnep1tcrallsfm01,
    i.sow_svep1actallsfm01,
    j.ctd_camptot06m,
    j.prm_camptot06m,
    j.max_camptot06m,
    j.min_camptot06m,
    j.rec_camptot06m,
    k.atm_monto,
    k.atm_frec,
    k.atm_recen,
    k.atm_trx_prom,
    k.atm_trx_ret_prom,
    k.atm_trx_dep,
    k.atm_trx_dep_prom,
    k.atm_trx_nmon_prom,
    k.atm_trx_nmon_prom2,
    k.atm_trx_nmon_min,
    k.atm_trx_con,
    k.atm_trx_con_prom,
    k.bpi_monto,
    k.bpi_trx_prom,
    k.bpi_trx_prom2,
    k.bpi_trx_nmon_prom,
    k.bpi_trx_nmon_prom2,
    k.bpi_trx_mon_prom,
    k.bpi_trx_mon_prom2,
    k.bpi_trx_mon_min,
    k.bpi_trx_mon_max,
    k.bpi_recen_mon,
    k.bpi_recen_nmon,
    k.grupo_final,
    m.lvl_edu,
    a.cod_mes as codmes 
FROM pd a
LEFT JOIN target b ON a.cod_cli = b.codunico AND CAST(a.cod_mes AS VARCHAR) = b.periodo_alerta
LEFT JOIN pd_02 c ON CAST(a.codmes_lag1 AS VARCHAR) = c.codmes AND a.key_value = c.key_value
LEFT JOIN pd_05 f ON CAST(a.codmes_lag1 AS VARCHAR) = f.p_codmes AND a.key_value = f.key_value
LEFT JOIN pd_06 g ON CAST(a.codmes_lag1 AS VARCHAR) = g.p_codmes AND a.key_value = g.key_value
LEFT JOIN pd_07 h ON CAST(a.codmes_lag1 AS VARCHAR) = h.p_codmes AND a.key_value = h.key_value
LEFT JOIN pd_08 i ON CAST(a.codmes_lag1 AS VARCHAR) = i.p_codmes AND a.key_value = i.key_value
LEFT JOIN pd_09 j ON CAST(a.codmes_lag1 AS VARCHAR) = j.p_codmes AND a.key_value = j.key_value
LEFT JOIN pd_10 k ON CAST(a.codmes_lag1 AS VARCHAR) = k.p_codmes AND a.key_value = k.key_value
LEFT JOIN pd_11 m ON CAST(a.codmes_lag1 AS VARCHAR) = m.p_codmes AND a.key_value = m.key_value)


select *
from pd_100