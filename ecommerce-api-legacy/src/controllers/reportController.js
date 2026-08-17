'use strict';

const toPositiveInt = (raw) => {
    if (raw === undefined) return undefined;
    const parsed = Number(raw);
    return Number.isInteger(parsed) ? parsed : undefined;
};

const makeReportController = ({ reportService }) => ({
    async financial(req, res) {
        const page = await reportService.financialReport({
            limit: toPositiveInt(req.query.limit),
            offset: toPositiveInt(req.query.offset),
        });
        return res.status(200).json(page);
    },
});

module.exports = { makeReportController };
