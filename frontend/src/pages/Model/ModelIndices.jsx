export default function ModelIndices({mse, mae, rmse, r2}) {
	return (
		<div className="flex flex-col p-6 bg-white shadow-lg rounded-lg">
			<h2 className="text-2xl font-bold text-gray-700 mb-4">모델 지표</h2>
			<div className="grid grid-cols-2 gap-4 text-center">
				<div className="p-4 bg-blue-100 rounded-lg">
					<p className="text-lg font-semibold text-gray-600">MSE</p>
					<p className="text-2xl font-bold text-blue-600">{mse}</p>
				</div>
				<div className="p-4 bg-green-100 rounded-lg">
					<p className="text-lg font-semibold text-gray-600">MAE</p>
					<p className="text-2xl font-bold text-green-600">{mae}</p>
				</div>
				<div className="p-4 bg-yellow-100 rounded-lg">
					<p className="text-lg font-semibold text-gray-600">RMSE</p>
					<p className="text-2xl font-bold text-yellow-600">{rmse}</p>
				</div>
				<div className="p-4 bg-purple-100 rounded-lg">
					<p className="text-lg font-semibold text-gray-600">R²</p>
					<p className="text-2xl font-bold text-purple-600">{r2}</p>
				</div>
			</div>
		</div>
	)
};