-- CTAS de inferencia para PLAFT PJ Minorista (universo BPE)
-- Actualizar PERIODO_INFERENCIA cuando corresponda.
CREATE TABLE "disc_comercial"."plaft_pj_minorista_202508" WITH (
     format = 'parquet',
  external_location = 's3://ibk-discovery-comercial-us-east-1-654654352211-data/discovery/comercial/sanherna/PLAFT/PJ/MINORISTA/DATA_INFERENCIA_PILOTO/INFERENCIA/',
  partitioned_by = ARRAY [ 'periodo' ]
) AS

WITH pd AS (
    SELECT DISTINCT
        a.key_value,
        a.cod_cli,
        a.cod_tip_doc,
        CAST(a.cod_mes AS INTEGER) AS cod_mes,

        TRY_CAST(a.mto_pas_soles AS DOUBLE) AS mto_pas_soles,
        TRY_CAST(a.imp_trx_abonosefect_6m AS DOUBLE) AS imp_trx_abonosefect_6m,
        TRY_CAST(a.imp_trx_cargosefe_6m AS DOUBLE) AS imp_trx_cargosefe_6m,
        TRY_CAST(a.avg_trx_cargostot_3m AS DOUBLE) AS avg_trx_cargostot_3m,
        TRY_CAST(a.cnt_trx_cargostot_3m AS INTEGER) AS cnt_trx_cargostot_3m,
        TRY_CAST(a.cnt_trx_abonospromtot_3m AS DOUBLE) AS cnt_trx_abonospromtot_3m,
        TRY_CAST(a.rat_trx_abonosefectot_3m AS DOUBLE) AS rat_trx_abonosefectot_3m,
        TRY_CAST(a.rat_trx_abonosefectot_1m AS DOUBLE) AS rat_trx_abonosefectot_1m,
        TRY_CAST(a.rat_mntcrgsefetot_1m AS DOUBLE) AS rat_mntcrgsefetot_1m,
        TRY_CAST(a.num_antiguedad AS INTEGER) AS num_antiguedad,
        TRY_CAST(a.cnt_meses_sinegresos_12m AS INTEGER) AS cnt_meses_sinegresos_12m,
        a.cod_ubigeo_cd,
        a.cod_sectorista_id,
        CAST(a.flg_vrcn_abonos_5m_1m AS INTEGER) AS flg_vrcn_abonos_5m_1m,
        a.mto_fact_declarado_sunat,
        TRY_CAST(a.avg_cp_men_ing_12m AS DOUBLE) AS avg_cp_men_ing_12m,
        TRY_CAST(a.avg_cpmenegr_12m AS DOUBLE) AS avg_cpmenegr_12m,
        TRY_CAST(a.max_mto_cpegrmen_12m AS DOUBLE) AS max_mto_cpegrmen_12m,
        TRY_CAST(a.cnt_trx_sinenv_alext_12m AS INTEGER) AS cnt_trx_sinenv_alext_12m,
        TRY_CAST(a.mto_al_ext_12m AS DOUBLE) AS mto_al_ext_12m,
        TRY_CAST(a.mto_del_ext_12m AS DOUBLE) AS mto_del_ext_12m,
        TRY_CAST(a.cnt_noticias AS INTEGER) AS cnt_noticias,
        a.flg_alerta_12m,
        TRY_CAST(a.cnt_alerta_hist AS INTEGER) AS cnt_alerta_hist,
        TRY_CAST(a.cnt_ros_hist AS INTEGER) AS cnt_ros_hist,
        TRY_CAST(a.avg_cpmenegr_12m AS DOUBLE)
            / NULLIF(TRY_CAST(a.imp_trx_cargostot_6m AS DOUBLE), 0)
            AS share_cp_egresos,
        TRY_CAST(a.avg_cp_men_ing_12m AS DOUBLE)
            / NULLIF(TRY_CAST(a.imp_trx_abonostot_6m AS DOUBLE), 0)
            AS share_cp_ingresos,
        TRY_CAST(a.mto_al_ext_12m AS DOUBLE)
            / NULLIF(TRY_CAST(a.imp_trx_abonostot_12m AS DOUBLE), 0)
            AS ratio_egresos_exterior,
        TRY_CAST(a.mto_pas_soles AS DOUBLE)
            / NULLIF(TRY_CAST(a.imp_trx_abonostot_6m AS DOUBLE), 0)
            AS rat_pastot_x_ingtot_6m,
        TRY_CAST(a.cnt_ros_hist AS DOUBLE)
            / NULLIF(TRY_CAST(a.cnt_trx_cargostot_3m AS DOUBLE), 0)
            AS rat_cntros_x_cnttrxegr_3m,
        TRY_CAST(a.mto_del_ext_12m AS DOUBLE)
            / NULLIF(TRY_CAST(a.imp_trx_abonostot_12m AS DOUBLE), 0)
            AS rat_ing_ext_x_ing_tot_12m,
        TRY_CAST(a.imp_trx_cargostot_1m AS DOUBLE)
            / NULLIF(TRY_CAST(a.avg_trx_cargostot_6m AS DOUBLE), 0)
            AS rat_cargos_1m_vs_6m

    FROM e_perm_aws.t_agg_alertas_plaft a
        WHERE a.cod_mes =  '202508'
      AND a.desc_subsegmento = 'BPE'
),

target AS (
    SELECT 
        codunico,
        periodo_alerta,
        tipo_alerta_n2,
        trx_riesgo_cliente,
        MAX(calificacion_monitoreo) AS flg_alerta
    FROM e_perm_aws.t_alertas_plaft
    GROUP BY codunico, periodo_alerta, tipo_alerta_n2,trx_riesgo_cliente
)

SELECT 
    a.*,
    b.tipo_alerta_n2,
    b.trx_riesgo_cliente,
    a.cod_mes as periodo
FROM pd a
LEFT JOIN target b
    ON a.cod_cli = b.codunico
    AND cast(a.cod_mes as varchar) = b.periodo_alerta